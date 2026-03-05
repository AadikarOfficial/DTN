from flask import Blueprint, request, jsonify, current_app
from models import Report
from database import db
import os
import secrets
import hashlib

whistle_bp = Blueprint("whistle", __name__)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "docx", "txt"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def secure_filename_custom(filename):
    """Strip path traversal and dangerous chars."""
    filename = os.path.basename(filename)
    # Remove anything outside safe characters
    safe = "".join(c for c in filename if c.isalnum() or c in "._-")
    return safe or "upload"


@whistle_bp.route("/api/report", methods=["POST"])
def submit_report():
    category = request.form.get("category", "").strip()
    level = request.form.get("level", "").strip()
    description = request.form.get("description", "").strip()

    if not category or not description:
        return jsonify({"error": "Category and description are required"}), 400

    if len(description) < 20:
        return jsonify({"error": "Description too short (min 20 characters)"}), 400

    # Generate anonymous tracking token
    case_token = secrets.token_hex(32)

    file = request.files.get("file")
    path = None

    if file and file.filename:
        if not allowed_file(file.filename):
            return jsonify({"error": f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(upload_folder, exist_ok=True)

        # Rename file to hash to prevent metadata leaks
        safe_name = secure_filename_custom(file.filename)
        ext = safe_name.rsplit(".", 1)[-1] if "." in safe_name else "bin"
        hashed_name = hashlib.sha256(os.urandom(32)).hexdigest()[:16] + f".{ext}"
        path = os.path.join(upload_folder, hashed_name)
        file.save(path)

    report = Report(
        category=category,
        level=level,
        description=description,
        file_path=path,
        case_token=case_token
    )

    db.session.add(report)
    db.session.commit()

    return jsonify({
        "message": "Report submitted anonymously",
        "case_token": case_token,
        "note": "Save this token to track your report. We cannot retrieve it if lost."
    }), 201


@whistle_bp.route("/api/report/track", methods=["GET"])
def track_report():
    token = request.args.get("token", "").strip()
    if not token or len(token) != 64:
        return jsonify({"error": "Valid 64-character case token required"}), 400

    report = Report.query.filter_by(case_token=token).first()
    if not report:
        return jsonify({"error": "Report not found"}), 404

    return jsonify({
        "case_token": token,
        "category": report.category,
        "status": report.status,
        "submitted_at": report.created_at.isoformat()
    })

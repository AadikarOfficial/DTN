from flask import Blueprint, request, jsonify
from models import Report
from database import db
import os

whistle_bp = Blueprint("whistle", __name__)

UPLOAD_FOLDER = "uploads"

@whistle_bp.route("/api/report", methods=["POST"])
def submit_report():

    category = request.form["category"]
    level = request.form["level"]
    description = request.form["description"]

    file = request.files.get("file")

    path = None

    if file:
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

    report = Report(
        category=category,
        level=level,
        description=description,
        file_path=path
    )

    db.session.add(report)
    db.session.commit()

    return jsonify({
        "message": "Report submitted",
        "case_id": report.id
    })

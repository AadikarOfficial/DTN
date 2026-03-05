from flask import Blueprint, request, jsonify
from models import Citizen
from database import db
from flask_jwt_extended import jwt_required, get_jwt_identity
import bcrypt
import re

citizen_bp = Blueprint("citizen", __name__)


def validate_citizenship_number(cn):
    # Basic format check
    return bool(cn and len(cn.strip()) >= 5)


def validate_mobile(mobile):
    return bool(re.match(r'^[9][6-9]\d{8}$', mobile))


@citizen_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required = ["full_name_nep", "full_name_eng", "dob", "gender",
                "province", "district", "municipality", "ward",
                "citizenship_number", "issued_district",
                "mobile", "password"]

    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Missing required field: {field}"}), 400

    cn = data["citizenship_number"].strip()
    if not validate_citizenship_number(cn):
        return jsonify({"error": "Invalid citizenship number format"}), 400

    # Check duplicate
    existing = Citizen.query.filter_by(citizenship_number=cn).first()
    if existing:
        return jsonify({"error": "Citizenship number already registered"}), 409

    password = data["password"]
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))

    citizen = Citizen(
        full_name_nep=data["full_name_nep"].strip(),
        full_name_eng=data["full_name_eng"].strip(),
        dob=data["dob"],
        gender=data["gender"],
        province=data["province"],
        district=data["district"],
        municipality=data["municipality"],
        ward=int(data["ward"]),
        citizenship_number=cn,
        issued_district=data["issued_district"],
        father_name=data.get("father_name", ""),
        mother_name=data.get("mother_name", ""),
        mobile=data["mobile"],
        password_hash=hashed
    )

    db.session.add(citizen)
    db.session.commit()

    return jsonify({
        "message": "Citizen registered successfully",
        "citizen_id": citizen.id
    }), 201


@citizen_bp.route("/api/citizens/<int:citizen_id>", methods=["GET"])
@jwt_required()
def get_citizen(citizen_id):
    current_user = int(get_jwt_identity())
    citizen = Citizen.query.get(citizen_id)

    if not citizen:
        return jsonify({"error": "Citizen not found"}), 404

    # Only allow viewing own profile or admin
    requester = Citizen.query.get(current_user)
    if current_user != citizen_id and requester.role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify({
        "id": citizen.id,
        "full_name_eng": citizen.full_name_eng,
        "full_name_nep": citizen.full_name_nep,
        "dob": citizen.dob,
        "gender": citizen.gender,
        "citizenship_number": citizen.citizenship_number,
        "province": citizen.province,
        "district": citizen.district,
        "municipality": citizen.municipality,
        "ward": citizen.ward,
        "mobile": citizen.mobile,
        "created_at": citizen.created_at.isoformat()
    })


@citizen_bp.route("/api/citizens", methods=["GET"])
@jwt_required()
def list_citizens():
    requester = Citizen.query.get(int(get_jwt_identity()))
    if not requester or requester.role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    citizens = Citizen.query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "total": citizens.total,
        "page": citizens.page,
        "pages": citizens.pages,
        "citizens": [{
            "id": c.id,
            "name": c.full_name_eng,
            "citizenship_number": c.citizenship_number,
            "district": c.district,
            "municipality": c.municipality
        } for c in citizens.items]
    })

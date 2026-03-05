from flask import Blueprint, request, jsonify
from models import Citizen
from database import db
from flask_jwt_extended import jwt_required, get_jwt_identity
import bcrypt, re

citizen_bp = Blueprint("citizen", __name__)


@citizen_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data: return jsonify({"error": "No data provided"}), 400
    required = ["full_name_nep","full_name_eng","dob","gender","province","district",
                "municipality","ward","citizenship_number","issued_district","mobile","password"]
    for f in required:
        if not data.get(f): return jsonify({"error": f"Missing required field: {f}"}), 400
    cn = data["citizenship_number"].strip()
    if len(cn) < 5: return jsonify({"error": "Invalid citizenship number"}), 400
    if Citizen.query.filter_by(citizenship_number=cn).first():
        return jsonify({"error": "Citizenship number already registered"}), 409
    pw = data["password"]
    if len(pw) < 8: return jsonify({"error": "Password must be at least 8 characters"}), 400
    hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12))
    c = Citizen(
        full_name_nep=data["full_name_nep"].strip(),
        full_name_eng=data["full_name_eng"].strip(),
        dob=data["dob"], gender=data["gender"],
        province=data["province"], district=data["district"],
        municipality=data["municipality"], ward=int(data["ward"]),
        citizenship_number=cn, issued_district=data["issued_district"],
        father_name=data.get("father_name",""), mother_name=data.get("mother_name",""),
        mobile=data["mobile"], email=data.get("email",""),
        password_hash=hashed, status="pending", role="citizen"
    )
    db.session.add(c); db.session.commit()
    return jsonify({"message": "Registration submitted. Awaiting admin approval.", "citizen_id": c.id}), 201


@citizen_bp.route("/api/me", methods=["GET"])
@jwt_required()
def get_me():
    c = Citizen.query.get(int(get_jwt_identity()))
    if not c: return jsonify({"error": "Not found"}), 404
    pos = None
    if c.position_id:
        from models import GovernmentPosition
        p = GovernmentPosition.query.get(c.position_id)
        if p: pos = {"title": p.title, "department": p.department or ""}
    return jsonify({
        "id": c.id, "full_name_eng": c.full_name_eng, "full_name_nep": c.full_name_nep,
        "citizenship_number": c.citizenship_number, "dob": c.dob, "gender": c.gender,
        "province": c.province, "district": c.district, "municipality": c.municipality,
        "ward": c.ward, "mobile": c.mobile, "email": c.email or "",
        "role": c.role, "status": c.status, "position": pos
    })

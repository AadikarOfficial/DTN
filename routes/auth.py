from flask import Blueprint, request, jsonify
from models import Citizen
from database import db
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import bcrypt

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    citizenship_number = data.get("citizenship_number", "").strip()
    password = data.get("password", "")

    if not citizenship_number or not password:
        return jsonify({"error": "Citizenship number and password are required"}), 400

    citizen = Citizen.query.filter_by(citizenship_number=citizenship_number).first()

    if not citizen or not citizen.is_active:
        return jsonify({"error": "Invalid credentials"}), 401

    # password_hash stored as bytes in DB (bcrypt returns bytes)
    stored_hash = citizen.password_hash
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode("utf-8")

    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(citizen.id))
    refresh_token = create_refresh_token(identity=str(citizen.id))

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "citizen": {
            "id": citizen.id,
            "name": citizen.full_name_eng,
            "role": citizen.role
        }
    })


@auth_bp.route("/api/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token})


@auth_bp.route("/api/me", methods=["GET"])
@jwt_required()
def get_me():
    citizen_id = get_jwt_identity()
    citizen = Citizen.query.get(int(citizen_id))
    if not citizen:
        return jsonify({"error": "Citizen not found"}), 404

    return jsonify({
        "id": citizen.id,
        "full_name_eng": citizen.full_name_eng,
        "full_name_nep": citizen.full_name_nep,
        "citizenship_number": citizen.citizenship_number,
        "province": citizen.province,
        "district": citizen.district,
        "municipality": citizen.municipality,
        "ward": citizen.ward,
        "mobile": citizen.mobile,
        "role": citizen.role
    })

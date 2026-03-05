from flask import Blueprint, request, jsonify
from models import Citizen
from database import db
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import bcrypt

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data: return jsonify({"error": "No data provided"}), 400
    cn = data.get("citizenship_number", "").strip()
    pw = data.get("password", "")
    if not cn or not pw: return jsonify({"error": "Citizenship number and password are required"}), 400
    citizen = Citizen.query.filter_by(citizenship_number=cn).first()
    if not citizen or not citizen.is_active:
        return jsonify({"error": "Invalid credentials"}), 401
    stored = citizen.password_hash
    if isinstance(stored, str): stored = stored.encode()
    if not bcrypt.checkpw(pw.encode(), stored):
        return jsonify({"error": "Invalid credentials"}), 401
    access_token  = create_access_token(identity=str(citizen.id))
    refresh_token = create_refresh_token(identity=str(citizen.id))
    return jsonify({
        "message": "Login successful",
        "access_token": access_token, "refresh_token": refresh_token,
        "citizen": {
            "id": citizen.id, "name": citizen.full_name_eng,
            "role": citizen.role, "status": citizen.status,
            "district": citizen.district
        }
    })


@auth_bp.route("/api/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    return jsonify({"access_token": create_access_token(identity=get_jwt_identity())})

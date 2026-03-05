from flask import Blueprint, request, jsonify
from models import Citizen
import bcrypt

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/api/login", methods=["POST"])
def login():

    data = request.json

    citizen = Citizen.query.filter_by(
        citizenship_number=data["citizenship_number"]
    ).first()

    if citizen and bcrypt.checkpw(
        data["password"].encode("utf-8"),
        citizen.password
    ):
        return jsonify({
            "message": "Login successful",
            "citizen_id": citizen.id
        })

    return jsonify({"error": "Invalid credentials"}), 401

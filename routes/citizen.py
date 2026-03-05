from flask import Blueprint, request, jsonify
from models import Citizen
from database import db
import bcrypt

citizen_bp = Blueprint("citizen", __name__)

@citizen_bp.route("/api/register", methods=["POST"])
def register():

    data = request.json

    hashed = bcrypt.hashpw(
        data["password"].encode("utf-8"),
        bcrypt.gensalt()
    )

    citizen = Citizen(
        full_name_nep=data["full_name_nep"],
        full_name_eng=data["full_name_eng"],
        dob=data["dob"],
        gender=data["gender"],
        province=data["province"],
        district=data["district"],
        municipality=data["municipality"],
        ward=data["ward"],
        citizenship_number=data["citizenship_number"],
        issued_district=data["issued_district"],
        father_name=data["father_name"],
        mother_name=data["mother_name"],
        mobile=data["mobile"],
        password=hashed
    )

    db.session.add(citizen)
    db.session.commit()

    return jsonify({"message": "Citizen registered successfully"})

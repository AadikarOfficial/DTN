from flask import Blueprint, request, jsonify
from models import Service, ServiceApplication, Citizen
from database import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

services_bp = Blueprint("services", __name__)


@services_bp.route("/api/services", methods=["GET"])
def get_services():
    services = Service.query.filter_by(is_active=True).all()
    return jsonify([{
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "department": s.department
    } for s in services])


@services_bp.route("/api/services/apply", methods=["POST"])
@jwt_required()
def apply_service():
    citizen_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or not data.get("service_id"):
        return jsonify({"error": "service_id is required"}), 400

    service = Service.query.get(data["service_id"])
    if not service or not service.is_active:
        return jsonify({"error": "Service not found"}), 404

    # Check for existing pending application
    existing = ServiceApplication.query.filter_by(
        citizen_id=citizen_id,
        service_id=data["service_id"],
        status="Pending"
    ).first()
    if existing:
        return jsonify({"error": "You already have a pending application for this service"}), 409

    application = ServiceApplication(
        citizen_id=citizen_id,
        service_id=data["service_id"]
    )
    db.session.add(application)
    db.session.commit()

    return jsonify({
        "message": "Application submitted successfully",
        "application_id": application.id
    }), 201


@services_bp.route("/api/services/my-applications", methods=["GET"])
@jwt_required()
def get_my_applications():
    citizen_id = int(get_jwt_identity())
    apps = ServiceApplication.query.filter_by(citizen_id=citizen_id).all()

    result = []
    for a in apps:
        service = Service.query.get(a.service_id)
        result.append({
            "application_id": a.id,
            "service": service.name if service else "Unknown",
            "department": service.department if service else "",
            "status": a.status,
            "notes": a.notes,
            "created_at": a.created_at.isoformat()
        })

    return jsonify(result)


@services_bp.route("/api/services/applications/<int:app_id>", methods=["PUT"])
@jwt_required()
def update_status(app_id):
    requester = Citizen.query.get(int(get_jwt_identity()))
    if not requester or requester.role not in ("admin", "officer"):
        return jsonify({"error": "Officer or admin access required"}), 403

    application = ServiceApplication.query.get(app_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404

    data = request.get_json()
    valid_statuses = ["Pending", "Processing", "Approved", "Rejected"]
    new_status = data.get("status")

    if new_status not in valid_statuses:
        return jsonify({"error": f"Status must be one of: {valid_statuses}"}), 400

    application.status = new_status
    application.notes = data.get("notes", application.notes)
    application.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Application status updated"})


@services_bp.route("/api/services", methods=["POST"])
@jwt_required()
def create_service():
    requester = Citizen.query.get(int(get_jwt_identity()))
    if not requester or requester.role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    if not data.get("name"):
        return jsonify({"error": "Service name is required"}), 400

    service = Service(
        name=data["name"],
        description=data.get("description", ""),
        department=data.get("department", "")
    )
    db.session.add(service)
    db.session.commit()

    return jsonify({"message": "Service created", "id": service.id}), 201

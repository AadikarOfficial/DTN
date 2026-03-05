from flask import Blueprint, request, jsonify
from models import Vote, Election, Candidate, Citizen
from database import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

voting_bp = Blueprint("voting", __name__)


@voting_bp.route("/api/elections", methods=["GET"])
def list_elections():
    elections = Election.query.all()
    result = []
    for e in elections:
        result.append({
            "id": e.id,
            "name": e.name,
            "type": e.election_type,
            "constituency": e.constituency,
            "province": e.province,
            "status": e.status,
            "start_date": e.start_date.isoformat() if e.start_date else None,
            "end_date": e.end_date.isoformat() if e.end_date else None
        })
    return jsonify(result)


@voting_bp.route("/api/elections/<int:election_id>", methods=["GET"])
def get_election(election_id):
    election = Election.query.get_or_404(election_id)
    candidates = [{
        "id": c.id,
        "name": c.name,
        "party": c.party,
        "symbol": c.symbol,
        "bio": c.bio
    } for c in election.candidates]

    return jsonify({
        "id": election.id,
        "name": election.name,
        "type": election.election_type,
        "status": election.status,
        "candidates": candidates
    })


@voting_bp.route("/api/vote", methods=["POST"])
@jwt_required()
def cast_vote():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    citizen_id = int(get_jwt_identity())
    candidate_id = data.get("candidate_id")
    election_id = data.get("election_id")

    if not candidate_id or not election_id:
        return jsonify({"error": "candidate_id and election_id are required"}), 400

    # Verify election is open
    election = Election.query.get(election_id)
    if not election:
        return jsonify({"error": "Election not found"}), 404
    if election.status != "open":
        return jsonify({"error": "Election is not currently open"}), 400

    # Verify candidate belongs to this election
    candidate = Candidate.query.filter_by(id=candidate_id, election_id=election_id).first()
    if not candidate:
        return jsonify({"error": "Candidate not found in this election"}), 404

    vote = Vote(
        citizen_id=citizen_id,
        candidate_id=candidate_id,
        election_id=election_id
    )

    try:
        db.session.add(vote)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "You have already voted in this election"}), 409

    return jsonify({"message": "Vote recorded successfully"}), 201


@voting_bp.route("/api/elections/<int:election_id>/results", methods=["GET"])
def get_results(election_id):
    election = Election.query.get_or_404(election_id)

    if election.status != "closed":
        return jsonify({"error": "Results only available after election closes"}), 400

    results = []
    for candidate in election.candidates:
        count = Vote.query.filter_by(
            candidate_id=candidate.id,
            election_id=election_id
        ).count()
        results.append({
            "candidate_id": candidate.id,
            "name": candidate.name,
            "party": candidate.party,
            "votes": count
        })

    results.sort(key=lambda x: x["votes"], reverse=True)
    total_votes = sum(r["votes"] for r in results)

    return jsonify({
        "election": election.name,
        "total_votes": total_votes,
        "results": results
    })


@voting_bp.route("/api/elections", methods=["POST"])
@jwt_required()
def create_election():
    requester = Citizen.query.get(int(get_jwt_identity()))
    if not requester or requester.role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    from datetime import datetime

    election = Election(
        name=data["name"],
        election_type=data.get("election_type", "local"),
        constituency=data.get("constituency"),
        province=data.get("province"),
        status=data.get("status", "upcoming"),
        start_date=datetime.fromisoformat(data["start_date"]) if data.get("start_date") else None,
        end_date=datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None
    )
    db.session.add(election)
    db.session.commit()

    return jsonify({"message": "Election created", "id": election.id}), 201

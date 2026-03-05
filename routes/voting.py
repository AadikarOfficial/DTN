from flask import Blueprint, request, jsonify
from models import Vote, Election, Candidate, Citizen
from database import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

voting_bp = Blueprint("voting", __name__)


@voting_bp.route("/api/elections", methods=["GET"])
def list_elections():
    elections = Election.query.order_by(Election.created_at.desc()).all()
    result = []
    for e in elections:
        online_votes = sum(Vote.query.filter_by(election_id=e.id).count() for _ in [1])
        result.append({
            "id": e.id, "name": e.name, "type": e.election_type,
            "constituency": e.constituency, "province": e.province,
            "district": e.district, "voting_mode": e.voting_mode or "online",
            "status": e.status, "description": e.description,
            "start_date": e.start_date.isoformat() if e.start_date else None,
            "end_date":   e.end_date.isoformat()   if e.end_date   else None,
            "candidate_count": len(e.candidates),
            "total_registered_voters": e.total_registered_voters or 0,
            "online_votes": online_votes,
        })
    return jsonify(result)


@voting_bp.route("/api/elections/<int:election_id>", methods=["GET"])
def get_election(election_id):
    e = Election.query.get_or_404(election_id)
    candidates = []
    for c in e.candidates:
        online = Vote.query.filter_by(candidate_id=c.id, election_id=election_id).count()
        candidates.append({
            "id": c.id, "name": c.name, "party": c.party or "Independent",
            "symbol": c.symbol, "bio": c.bio, "age": c.age,
            "gender": c.gender, "district": c.district,
            "online_votes": online if e.status == "closed" else None,
            "paper_votes":  c.paper_votes if e.status == "closed" else None,
        })
    return jsonify({
        "id": e.id, "name": e.name, "type": e.election_type,
        "status": e.status, "voting_mode": e.voting_mode or "online",
        "province": e.province, "district": e.district,
        "constituency": e.constituency, "description": e.description,
        "candidates": candidates,
        "total_registered_voters": e.total_registered_voters or 0,
    })


@voting_bp.route("/api/vote", methods=["POST"])
@jwt_required()
def cast_vote():
    data       = request.get_json()
    citizen_id = int(get_jwt_identity())
    if not data:
        return jsonify({"error": "No data provided"}), 400
    candidate_id = data.get("candidate_id")
    election_id  = data.get("election_id")
    if not candidate_id or not election_id:
        return jsonify({"error": "candidate_id and election_id required"}), 400

    citizen = Citizen.query.get(citizen_id)
    if not citizen or citizen.status != "approved":
        return jsonify({"error": "Your account must be approved to vote"}), 403

    election = Election.query.get(election_id)
    if not election:
        return jsonify({"error": "Election not found"}), 404
    if election.status != "open":
        return jsonify({"error": "Election is not currently open"}), 400
    if election.voting_mode == "paper":
        return jsonify({"error": "This election uses paper ballots only"}), 400

    # District-based eligibility: if election has a district set, voter must match
    if election.district and citizen.district.lower() != election.district.lower():
        return jsonify({"error": f"You are not registered in {election.district} and cannot vote in this election"}), 403

    candidate = Candidate.query.filter_by(id=candidate_id, election_id=election_id).first()
    if not candidate:
        return jsonify({"error": "Candidate not found in this election"}), 404

    vote = Vote(citizen_id=citizen_id, candidate_id=candidate_id, election_id=election_id)
    try:
        db.session.add(vote); db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "You have already voted in this election"}), 409

    return jsonify({"message": "Vote recorded successfully"}), 201


@voting_bp.route("/api/elections/<int:election_id>/results", methods=["GET"])
def get_results(election_id):
    e = Election.query.get_or_404(election_id)
    if e.status != "closed":
        return jsonify({"error": "Results only available after election closes"}), 400
    results = []
    for c in e.candidates:
        online = Vote.query.filter_by(candidate_id=c.id, election_id=election_id).count()
        paper  = c.paper_votes or 0
        total  = online + paper if e.voting_mode == "hybrid" else (paper if e.voting_mode == "paper" else online)
        results.append({
            "candidate_id": c.id, "name": c.name, "party": c.party or "Independent",
            "online_votes": online, "paper_votes": paper, "total_votes": total
        })
    results.sort(key=lambda x: x["total_votes"], reverse=True)
    total_votes = sum(r["total_votes"] for r in results)
    discrepancy = None
    if e.voting_mode == "hybrid" and total_votes > 0:
        online_total = sum(r["online_votes"] for r in results)
        paper_total  = sum(r["paper_votes"] for r in results)
        discrepancy  = abs(online_total - paper_total)
    return jsonify({
        "election": e.name, "voting_mode": e.voting_mode,
        "total_votes": total_votes, "results": results,
        "discrepancy": discrepancy,
        "registered_voters": e.total_registered_voters or 0
    })


@voting_bp.route("/api/elections/<int:election_id>/my-vote", methods=["GET"])
@jwt_required()
def my_vote(election_id):
    citizen_id = int(get_jwt_identity())
    v = Vote.query.filter_by(citizen_id=citizen_id, election_id=election_id).first()
    if not v: return jsonify({"voted": False})
    c = Candidate.query.get(v.candidate_id)
    return jsonify({"voted": True, "candidate": c.name if c else "?", "party": c.party if c else ""})

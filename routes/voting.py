from flask import Blueprint, request, jsonify
from models import Vote
from database import db

voting_bp = Blueprint("voting", __name__)

@voting_bp.route("/api/vote", methods=["POST"])
def cast_vote():

    data = request.json

    vote = Vote(
        citizen_id=data["citizen_id"],
        candidate_id=data["candidate_id"],
        election_id=data["election_id"]
    )

    db.session.add(vote)
    db.session.commit()

    return jsonify({"message": "Vote recorded successfully"})

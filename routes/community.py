from flask import Blueprint, request, jsonify
from models import CommunityPost, Citizen
from database import db
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError

community_bp = Blueprint("community", __name__)


@community_bp.route("/api/community", methods=["GET"])
def list_posts():
    page     = request.args.get("page", 1, type=int)
    category = request.args.get("category", "")
    q = CommunityPost.query.filter_by(is_hidden=False)
    if category: q = q.filter_by(category=category)
    q = q.order_by(CommunityPost.is_pinned.desc(), CommunityPost.created_at.desc())
    pag = q.paginate(page=page, per_page=10, error_out=False)
    return jsonify({
        "total": pag.total, "pages": pag.pages,
        "posts": [_post_row(p) for p in pag.items]
    })


@community_bp.route("/api/community", methods=["POST"])
@jwt_required()
def create_post():
    cid  = int(get_jwt_identity())
    citizen = Citizen.query.get(cid)
    if not citizen or citizen.status != "approved":
        return jsonify({"error": "Only approved citizens can post"}), 403
    data = request.get_json()
    if not data.get("title") or not data.get("content"):
        return jsonify({"error": "Title and content required"}), 400
    if len(data["content"]) < 10:
        return jsonify({"error": "Content too short"}), 400
    p = CommunityPost(
        citizen_id=cid,
        title=data["title"][:300],
        content=data["content"],
        category=data.get("category", "general")
    )
    db.session.add(p); db.session.commit()
    return jsonify({"id": p.id, "message": "Post published"}), 201


@community_bp.route("/api/community/<int:pid>/like", methods=["POST"])
@jwt_required()
def like_post(pid):
    p = CommunityPost.query.get_or_404(pid)
    p.likes += 1
    db.session.commit()
    return jsonify({"likes": p.likes})


@community_bp.route("/api/community/<int:pid>", methods=["DELETE"])
@jwt_required()
def delete_post(pid):
    cid = int(get_jwt_identity())
    p   = CommunityPost.query.get_or_404(pid)
    c   = Citizen.query.get(cid)
    if p.citizen_id != cid and c.role not in ("admin", "officer"):
        return jsonify({"error": "Unauthorized"}), 403
    db.session.delete(p); db.session.commit()
    return jsonify({"message": "Deleted"})


def _post_row(p):
    citizen = Citizen.query.get(p.citizen_id)
    return {
        "id": p.id, "title": p.title, "content": p.content,
        "category": p.category, "likes": p.likes,
        "is_pinned": p.is_pinned,
        "author": citizen.full_name_eng if citizen else "Anonymous",
        "district": citizen.district if citizen else "",
        "created_at": p.created_at.isoformat()
    }

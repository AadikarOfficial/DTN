import csv, os, io
from flask import Blueprint, request, jsonify, current_app
from models import (Citizen, Election, Candidate, Vote, Report,
                    Service, ServiceApplication, CommunityPost,
                    Role, GovernmentPosition, CandidatePool)
from database import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import func

admin_bp = Blueprint("admin", __name__)


def require_admin():
    c = Citizen.query.get(int(get_jwt_identity()))
    if not c or c.role != "admin":
        return None, (jsonify({"error": "Admin access required"}), 403)
    return c, None


# ── STATS ──────────────────────────────────────────────────────
@admin_bp.route("/api/admin/stats", methods=["GET"])
@jwt_required()
def stats():
    _, err = require_admin()
    if err: return err
    total_c   = Citizen.query.count()
    pending_c = Citizen.query.filter_by(status="pending").count()
    approved_c= Citizen.query.filter_by(status="approved").count()
    total_e   = Election.query.count()
    open_e    = Election.query.filter_by(status="open").count()
    total_v   = Vote.query.count()
    total_r   = Report.query.count()
    pending_r = Report.query.filter_by(status="received").count()
    total_svc = ServiceApplication.query.count()
    pending_s = ServiceApplication.query.filter_by(status="Pending").count()
    pool_total= CandidatePool.query.count()
    return jsonify({
        "citizens":  {"total": total_c, "pending": pending_c, "approved": approved_c},
        "elections": {"total": total_e, "open": open_e, "total_votes": total_v},
        "reports":   {"total": total_r, "pending": pending_r},
        "services":  {"total_applications": total_svc, "pending": pending_s},
        "candidate_pool": {"total": pool_total}
    })


# ── CITIZENS ───────────────────────────────────────────────────
@admin_bp.route("/api/admin/citizens", methods=["GET"])
@jwt_required()
def list_citizens():
    _, err = require_admin()
    if err: return err
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status   = request.args.get("status", "")
    search   = request.args.get("search", "")
    q = Citizen.query
    if status: q = q.filter_by(status=status)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (Citizen.full_name_eng.ilike(like)) |
            (Citizen.citizenship_number.ilike(like)) |
            (Citizen.district.ilike(like)) |
            (Citizen.mobile.ilike(like))
        )
    pag = q.order_by(Citizen.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "total": pag.total, "page": pag.page, "pages": pag.pages,
        "citizens": [_citizen_row(c) for c in pag.items]
    })


@admin_bp.route("/api/admin/citizens/<int:cid>", methods=["GET"])
@jwt_required()
def get_citizen(cid):
    _, err = require_admin()
    if err: return err
    c = Citizen.query.get_or_404(cid)
    pos = None
    if c.position_id:
        p = GovernmentPosition.query.get(c.position_id)
        if p: pos = {"title": p.title, "department": p.department or ""}
    return jsonify({**_citizen_row(c),
        "dob": c.dob, "gender": c.gender, "father_name": c.father_name,
        "mother_name": c.mother_name, "municipality": c.municipality,
        "ward": c.ward, "issued_district": c.issued_district,
        "email": c.email or "", "rejection_reason": c.rejection_reason or "",
        "position": pos
    })


@admin_bp.route("/api/admin/citizens/<int:cid>/approve", methods=["POST"])
@jwt_required()
def approve_citizen(cid):
    _, err = require_admin()
    if err: return err
    c = Citizen.query.get_or_404(cid)
    c.status = "approved"
    c.rejection_reason = None
    db.session.commit()
    return jsonify({"message": "Citizen approved"})


@admin_bp.route("/api/admin/citizens/<int:cid>/reject", methods=["POST"])
@jwt_required()
def reject_citizen(cid):
    _, err = require_admin()
    if err: return err
    c = Citizen.query.get_or_404(cid)
    c.status = "rejected"
    c.rejection_reason = request.get_json(silent=True).get("reason", "") if request.get_json(silent=True) else ""
    db.session.commit()
    return jsonify({"message": "Citizen rejected"})


@admin_bp.route("/api/admin/citizens/<int:cid>/role", methods=["POST"])
@jwt_required()
def set_role(cid):
    _, err = require_admin()
    if err: return err
    data = request.get_json()
    role = data.get("role", "citizen")
    if role not in ("citizen", "officer", "admin"):
        return jsonify({"error": "Invalid role"}), 400
    c = Citizen.query.get_or_404(cid)
    c.role = role
    db.session.commit()
    return jsonify({"message": f"Role set to {role}"})


@admin_bp.route("/api/admin/citizens/<int:cid>/position", methods=["POST"])
@jwt_required()
def assign_position(cid):
    _, err = require_admin()
    if err: return err
    data = request.get_json()
    pos_id = data.get("position_id")
    c = Citizen.query.get_or_404(cid)
    if pos_id:
        pos = GovernmentPosition.query.get_or_404(int(pos_id))
        pos.holder_id = cid
        c.position_id = pos.id
    else:
        if c.position_id:
            old = GovernmentPosition.query.get(c.position_id)
            if old: old.holder_id = None
        c.position_id = None
    db.session.commit()
    return jsonify({"message": "Position updated"})


# ── ROLES ──────────────────────────────────────────────────────
@admin_bp.route("/api/admin/roles", methods=["GET"])
@jwt_required()
def list_roles():
    _, err = require_admin()
    if err: return err
    return jsonify([{"id": r.id, "name": r.name, "description": r.description, "permissions": r.permissions} for r in Role.query.all()])


@admin_bp.route("/api/admin/roles", methods=["POST"])
@jwt_required()
def create_role():
    _, err = require_admin()
    if err: return err
    data = request.get_json()
    if not data.get("name"): return jsonify({"error": "Name required"}), 400
    if Role.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "Role name already exists"}), 409
    r = Role(name=data["name"], description=data.get("description", ""), permissions=data.get("permissions", "[]"))
    db.session.add(r); db.session.commit()
    return jsonify({"id": r.id, "message": "Role created"}), 201


@admin_bp.route("/api/admin/roles/<int:rid>", methods=["PUT"])
@jwt_required()
def update_role(rid):
    _, err = require_admin()
    if err: return err
    r = Role.query.get_or_404(rid)
    data = request.get_json()
    r.name = data.get("name", r.name)
    r.description = data.get("description", r.description)
    r.permissions = data.get("permissions", r.permissions)
    db.session.commit()
    return jsonify({"message": "Role updated"})


@admin_bp.route("/api/admin/roles/<int:rid>", methods=["DELETE"])
@jwt_required()
def delete_role(rid):
    _, err = require_admin()
    if err: return err
    r = Role.query.get_or_404(rid)
    db.session.delete(r); db.session.commit()
    return jsonify({"message": "Deleted"})


# ── POSITIONS ──────────────────────────────────────────────────
@admin_bp.route("/api/admin/positions", methods=["GET"])
@jwt_required()
def list_positions():
    _, err = require_admin()
    if err: return err
    positions = GovernmentPosition.query.all()
    result = []
    for p in positions:
        role_obj = Role.query.get(p.role_id) if p.role_id else None
        holder = Citizen.query.get(p.holder_id) if p.holder_id else None
        result.append({
            "id": p.id, "title": p.title, "department": p.department,
            "level": p.level, "province": p.province, "district": p.district,
            "municipality": p.municipality,
            "role": {"id": role_obj.id, "name": role_obj.name} if role_obj else None,
            "holder": holder.full_name_eng if holder else None
        })
    return jsonify(result)


@admin_bp.route("/api/admin/positions", methods=["POST"])
@jwt_required()
def create_position():
    _, err = require_admin()
    if err: return err
    data = request.get_json()
    if not data.get("title"): return jsonify({"error": "Title required"}), 400
    p = GovernmentPosition(
        title=data["title"], department=data.get("department"),
        level=data.get("level", "municipal"), province=data.get("province"),
        district=data.get("district"), municipality=data.get("municipality"),
        role_id=int(data["role_id"]) if data.get("role_id") else None
    )
    db.session.add(p); db.session.commit()
    return jsonify({"id": p.id, "message": "Position created"}), 201


@admin_bp.route("/api/admin/positions/<int:pid>", methods=["DELETE"])
@jwt_required()
def delete_position(pid):
    _, err = require_admin()
    if err: return err
    p = GovernmentPosition.query.get_or_404(pid)
    # Unlink holder
    if p.holder_id:
        c = Citizen.query.get(p.holder_id)
        if c: c.position_id = None
    db.session.delete(p); db.session.commit()
    return jsonify({"message": "Deleted"})


# ── ELECTIONS ──────────────────────────────────────────────────
@admin_bp.route("/api/admin/elections", methods=["POST"])
@jwt_required()
def create_election():
    _, err = require_admin()
    if err: return err
    data = request.get_json()
    if not data.get("name"): return jsonify({"error": "Name required"}), 400
    e = Election(
        name=data["name"], election_type=data.get("election_type", "local"),
        constituency=data.get("constituency"), province=data.get("province"),
        district=data.get("district"), voting_mode=data.get("voting_mode", "online"),
        status=data.get("status", "upcoming"), description=data.get("description"),
        total_registered_voters=int(data.get("total_registered_voters") or 0),
        start_date=_parse_dt(data.get("start_date")),
        end_date=_parse_dt(data.get("end_date"))
    )
    db.session.add(e); db.session.commit()
    return jsonify({"id": e.id, "message": "Election created"}), 201


@admin_bp.route("/api/admin/elections/<int:eid>", methods=["PUT"])
@jwt_required()
def update_election(eid):
    _, err = require_admin()
    if err: return err
    e = Election.query.get_or_404(eid)
    data = request.get_json()
    e.name = data.get("name", e.name)
    e.election_type = data.get("election_type", e.election_type)
    e.constituency = data.get("constituency", e.constituency)
    e.province = data.get("province", e.province)
    e.district = data.get("district", e.district)
    e.voting_mode = data.get("voting_mode", e.voting_mode)
    e.status = data.get("status", e.status)
    e.description = data.get("description", e.description)
    e.total_registered_voters = int(data.get("total_registered_voters") or e.total_registered_voters or 0)
    if data.get("start_date"): e.start_date = _parse_dt(data["start_date"])
    if data.get("end_date"):   e.end_date   = _parse_dt(data["end_date"])
    db.session.commit()
    return jsonify({"message": "Updated"})


@admin_bp.route("/api/admin/elections/<int:eid>", methods=["DELETE"])
@jwt_required()
def delete_election(eid):
    _, err = require_admin()
    if err: return err
    e = Election.query.get_or_404(eid)
    db.session.delete(e); db.session.commit()
    return jsonify({"message": "Deleted"})


@admin_bp.route("/api/admin/elections/<int:eid>/candidates", methods=["POST"])
@jwt_required()
def add_candidate(eid):
    _, err = require_admin()
    if err: return err
    data = request.get_json()
    if not data.get("name"): return jsonify({"error": "Name required"}), 400
    e = Election.query.get_or_404(eid)
    c = Candidate(
        name=data["name"], party=data.get("party"), symbol=data.get("symbol"),
        age=int(data["age"]) if data.get("age") else None, gender=data.get("gender"),
        district=data.get("district") or e.district, province=data.get("province") or e.province,
        election_id=eid, source="manual"
    )
    db.session.add(c); db.session.commit()
    return jsonify({"id": c.id, "message": "Candidate added"}), 201


@admin_bp.route("/api/admin/elections/<int:eid>/candidates/<int:cid>", methods=["DELETE"])
@jwt_required()
def remove_candidate(eid, cid):
    _, err = require_admin()
    if err: return err
    c = Candidate.query.filter_by(id=cid, election_id=eid).first_or_404()
    db.session.delete(c); db.session.commit()
    return jsonify({"message": "Removed"})


@admin_bp.route("/api/admin/elections/<int:eid>/candidates/import-csv", methods=["POST"])
@jwt_required()
def import_candidates_csv(eid):
    _, err = require_admin()
    if err: return err
    if CandidatePool.query.count() == 0:
        return jsonify({"error": "Candidate pool is empty. Import CSV first."}), 400
    e = Election.query.get_or_404(eid)
    data = request.get_json(silent=True) or {}
    party    = data.get("party", "").strip()
    province = data.get("province", "").strip()
    district = data.get("district", "").strip()
    limit    = min(int(data.get("limit", 10)), 100)
    q = CandidatePool.query
    if party:    q = q.filter(CandidatePool.party.ilike(f"%{party}%"))
    if province: q = q.filter(CandidatePool.province.ilike(f"%{province}%"))
    if district: q = q.filter(CandidatePool.district.ilike(f"%{district}%"))
    existing_csv_ids = {c.csv_candidate_id for c in Candidate.query.filter_by(election_id=eid).all() if c.csv_candidate_id}
    pool = [p for p in q.limit(limit * 3).all() if p.candidate_id not in existing_csv_ids][:limit]
    added = 0
    for p in pool:
        c = Candidate(
            name=p.name, party=p.party, age=p.age, gender=p.gender,
            district=p.district, province=p.province,
            election_id=eid, source="csv", csv_candidate_id=p.candidate_id
        )
        db.session.add(c); added += 1
    db.session.commit()
    return jsonify({"message": f"Imported {added} candidates from pool"})


@admin_bp.route("/api/admin/elections/<int:eid>/paper-results", methods=["POST"])
@jwt_required()
def save_paper_results(eid):
    _, err = require_admin()
    if err: return err
    data = request.get_json()
    results = data.get("results", [])
    for r in results:
        cid = r.get("candidate_id")
        votes = int(r.get("votes_count", 0))
        c = Candidate.query.filter_by(id=cid, election_id=eid).first()
        if c: c.paper_votes = votes
    db.session.commit()
    return jsonify({"message": "Paper results saved"})


# ── CANDIDATE POOL ─────────────────────────────────────────────
@admin_bp.route("/api/admin/candidate-pool/import", methods=["POST"])
@jwt_required()
def import_pool():
    _, err = require_admin()
    if err: return err
    csv_path = "/mnt/user-data/uploads/nepal_synthetic_candidate_dataset_50k.csv"
    if not os.path.exists(csv_path):
        return jsonify({"error": "CSV file not found on server"}), 404
    CandidatePool.query.delete()
    count = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            batch.append(CandidatePool(
                candidate_id=row.get("candidate_id", ""),
                name=row.get("name", ""),
                age=int(row["age"]) if row.get("age", "").isdigit() else None,
                gender=row.get("gender"),
                party=row.get("party"),
                province=row.get("province"),
                district=row.get("district"),
                ward=int(row["ward"]) if row.get("ward", "").isdigit() else None,
            ))
            count += 1
            if len(batch) >= 1000:
                db.session.bulk_save_objects(batch); batch = []
        if batch: db.session.bulk_save_objects(batch)
    db.session.commit()
    return jsonify({"message": f"Imported {count:,} candidates into pool"})


@admin_bp.route("/api/admin/candidate-pool", methods=["GET"])
@jwt_required()
def list_pool():
    _, err = require_admin()
    if err: return err
    page     = request.args.get("page", 1, type=int)
    search   = request.args.get("search", "")
    party    = request.args.get("party", "")
    province = request.args.get("province", "")
    district = request.args.get("district", "")
    q = CandidatePool.query
    if search:   q = q.filter(CandidatePool.name.ilike(f"%{search}%"))
    if party:    q = q.filter(CandidatePool.party.ilike(f"%{party}%"))
    if province: q = q.filter(CandidatePool.province.ilike(f"%{province}%"))
    if district: q = q.filter(CandidatePool.district.ilike(f"%{district}%"))
    pag = q.paginate(page=page, per_page=25, error_out=False)
    return jsonify({
        "total": pag.total, "pages": pag.pages, "page": pag.page,
        "candidates": [{"id": c.id, "candidate_id": c.candidate_id, "name": c.name,
                        "age": c.age, "gender": c.gender, "party": c.party,
                        "province": c.province, "district": c.district, "ward": c.ward}
                       for c in pag.items]
    })


@admin_bp.route("/api/admin/candidate-pool/parties", methods=["GET"])
@jwt_required()
def pool_parties():
    _, err = require_admin()
    if err: return err
    rows = db.session.query(CandidatePool.party, func.count(CandidatePool.id))\
        .group_by(CandidatePool.party).order_by(func.count(CandidatePool.id).desc()).all()
    return jsonify([{"party": r[0], "count": r[1]} for r in rows if r[0]])


# ── REPORTS ────────────────────────────────────────────────────
@admin_bp.route("/api/admin/reports", methods=["GET"])
@jwt_required()
def list_reports():
    _, err = require_admin()
    if err: return err
    page   = request.args.get("page", 1, type=int)
    status = request.args.get("status", "")
    q = Report.query
    if status: q = q.filter_by(status=status)
    pag = q.order_by(Report.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return jsonify({
        "total": pag.total, "pages": pag.pages,
        "reports": [{"id": r.id, "category": r.category, "level": r.level,
                     "status": r.status, "created_at": r.created_at.isoformat(),
                     "has_file": bool(r.file_path)} for r in pag.items]
    })


@admin_bp.route("/api/admin/reports/<int:rid>", methods=["GET"])
@jwt_required()
def get_report(rid):
    _, err = require_admin()
    if err: return err
    r = Report.query.get_or_404(rid)
    return jsonify({
        "id": r.id, "category": r.category, "level": r.level,
        "description": r.description, "status": r.status,
        "admin_notes": r.admin_notes or "", "created_at": r.created_at.isoformat(),
        "has_file": bool(r.file_path), "case_token": r.case_token
    })


@admin_bp.route("/api/admin/reports/<int:rid>", methods=["PUT"])
@jwt_required()
def update_report(rid):
    _, err = require_admin()
    if err: return err
    r = Report.query.get_or_404(rid)
    data = request.get_json()
    r.status = data.get("status", r.status)
    r.admin_notes = data.get("admin_notes", r.admin_notes)
    db.session.commit()
    return jsonify({"message": "Updated"})


# ── SERVICE APPLICATIONS ───────────────────────────────────────
@admin_bp.route("/api/admin/service-applications", methods=["GET"])
@jwt_required()
def list_svc_apps():
    _, err = require_admin()
    if err: return err
    page   = request.args.get("page", 1, type=int)
    status = request.args.get("status", "")
    q = ServiceApplication.query
    if status: q = q.filter_by(status=status)
    pag = q.order_by(ServiceApplication.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    result = []
    for a in pag.items:
        c = Citizen.query.get(a.citizen_id)
        s = Service.query.get(a.service_id)
        result.append({
            "id": a.id, "citizen": c.full_name_eng if c else "?",
            "citizenship_number": c.citizenship_number if c else "",
            "service": s.name if s else "?", "department": s.department if s else "",
            "status": a.status, "notes": a.notes or "",
            "created_at": a.created_at.isoformat()
        })
    return jsonify({"total": pag.total, "pages": pag.pages, "applications": result})


@admin_bp.route("/api/admin/service-applications/<int:aid>", methods=["PUT"])
@jwt_required()
def update_svc_app(aid):
    _, err = require_admin()
    if err: return err
    a = ServiceApplication.query.get_or_404(aid)
    data = request.get_json()
    a.status = data.get("status", a.status)
    a.notes  = data.get("notes", a.notes)
    db.session.commit()
    return jsonify({"message": "Updated"})


# ── COMMUNITY ──────────────────────────────────────────────────
@admin_bp.route("/api/admin/community", methods=["GET"])
@jwt_required()
def list_community():
    _, err = require_admin()
    if err: return err
    page = request.args.get("page", 1, type=int)
    pag  = CommunityPost.query.order_by(CommunityPost.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    result = []
    for p in pag.items:
        c = Citizen.query.get(p.citizen_id)
        result.append({
            "id": p.id, "title": p.title, "category": p.category,
            "likes": p.likes, "is_pinned": p.is_pinned, "is_hidden": p.is_hidden,
            "author": c.full_name_eng if c else "?",
            "created_at": p.created_at.isoformat()
        })
    return jsonify({"total": pag.total, "pages": pag.pages, "posts": result})


@admin_bp.route("/api/admin/community/<int:pid>/pin", methods=["POST"])
@jwt_required()
def pin_post(pid):
    _, err = require_admin()
    if err: return err
    p = CommunityPost.query.get_or_404(pid)
    p.is_pinned = not p.is_pinned
    db.session.commit()
    return jsonify({"is_pinned": p.is_pinned})


@admin_bp.route("/api/admin/community/<int:pid>/hide", methods=["POST"])
@jwt_required()
def hide_post(pid):
    _, err = require_admin()
    if err: return err
    p = CommunityPost.query.get_or_404(pid)
    p.is_hidden = not p.is_hidden
    db.session.commit()
    return jsonify({"is_hidden": p.is_hidden})


@admin_bp.route("/api/admin/community/<int:pid>", methods=["DELETE"])
@jwt_required()
def delete_post(pid):
    _, err = require_admin()
    if err: return err
    p = CommunityPost.query.get_or_404(pid)
    db.session.delete(p); db.session.commit()
    return jsonify({"message": "Deleted"})


# ── HELPERS ────────────────────────────────────────────────────
def _citizen_row(c):
    return {
        "id": c.id, "full_name_eng": c.full_name_eng, "full_name_nep": c.full_name_nep,
        "citizenship_number": c.citizenship_number, "district": c.district,
        "province": c.province, "mobile": c.mobile, "email": c.email or "",
        "role": c.role, "status": c.status, "created_at": c.created_at.isoformat()
    }


def _parse_dt(s):
    if not s: return None
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try: return datetime.strptime(s, fmt)
        except: pass
    return None

from database import db
from datetime import datetime


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(500))
    permissions = db.Column(db.Text, default="[]")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class GovernmentPosition(db.Model):
    __tablename__ = "government_positions"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(200))
    level = db.Column(db.String(50))
    province = db.Column(db.String(100))
    district = db.Column(db.String(100))
    municipality = db.Column(db.String(100))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=True)
    holder_id = db.Column(db.Integer, db.ForeignKey("citizens.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Citizen(db.Model):
    __tablename__ = "citizens"
    id = db.Column(db.Integer, primary_key=True)
    full_name_nep = db.Column(db.String(200), nullable=False)
    full_name_eng = db.Column(db.String(200), nullable=False)
    dob = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    province = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    municipality = db.Column(db.String(100), nullable=False)
    ward = db.Column(db.Integer, nullable=False)
    citizenship_number = db.Column(db.String(50), unique=True, nullable=False)
    issued_district = db.Column(db.String(100), nullable=False)
    father_name = db.Column(db.String(200))
    mother_name = db.Column(db.String(200))
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(200))
    password_hash = db.Column(db.String(300), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(50), default="citizen")
    status = db.Column(db.String(50), default="pending")
    rejection_reason = db.Column(db.Text)
    position_id = db.Column(db.Integer, db.ForeignKey("government_positions.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Election(db.Model):
    __tablename__ = "elections"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    election_type = db.Column(db.String(100))
    constituency = db.Column(db.String(200))
    province = db.Column(db.String(100))
    district = db.Column(db.String(100))
    voting_mode = db.Column(db.String(50), default="online")
    status = db.Column(db.String(50), default="upcoming")
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    total_registered_voters = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    candidates = db.relationship("Candidate", backref="election", lazy=True, cascade="all, delete-orphan")
    votes = db.relationship("Vote", backref="election", lazy=True, cascade="all, delete-orphan")


class Candidate(db.Model):
    __tablename__ = "candidates"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    party = db.Column(db.String(200))
    symbol = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    district = db.Column(db.String(100))
    province = db.Column(db.String(100))
    bio = db.Column(db.Text)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    source = db.Column(db.String(50), default="manual")
    csv_candidate_id = db.Column(db.String(50))
    paper_votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Vote(db.Model):
    __tablename__ = "votes"
    id = db.Column(db.Integer, primary_key=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey("citizens.id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    __table_args__ = (db.UniqueConstraint("citizen_id", "election_id", name="unique_citizen_election_vote"),)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class CandidatePool(db.Model):
    __tablename__ = "candidate_pool"
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    party = db.Column(db.String(200))
    province = db.Column(db.String(100))
    district = db.Column(db.String(100))
    ward = db.Column(db.Integer)


class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(200), nullable=False)
    level = db.Column(db.String(200))
    description = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(300))
    status = db.Column(db.String(50), default="received")
    admin_notes = db.Column(db.Text)
    case_token = db.Column(db.String(64), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Service(db.Model):
    __tablename__ = "services"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    department = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)


class ServiceApplication(db.Model):
    __tablename__ = "service_applications"
    id = db.Column(db.Integer, primary_key=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey("citizens.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CommunityPost(db.Model):
    __tablename__ = "community_posts"
    id = db.Column(db.Integer, primary_key=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey("citizens.id"), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), default="general")
    likes = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    is_hidden = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

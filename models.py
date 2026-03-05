from database import db
from datetime import datetime


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
    password_hash = db.Column(db.String(300), nullable=False)  # renamed from 'password'

    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(50), default="citizen")  # citizen, admin, officer

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Election(db.Model):
    __tablename__ = "elections"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    election_type = db.Column(db.String(100))   # federal, provincial, local
    constituency = db.Column(db.String(200))
    province = db.Column(db.String(100))
    status = db.Column(db.String(50), default="upcoming")  # upcoming, open, closed
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    candidates = db.relationship("Candidate", backref="election", lazy=True)
    votes = db.relationship("Vote", backref="election", lazy=True)


class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    party = db.Column(db.String(200))
    symbol = db.Column(db.String(100))
    bio = db.Column(db.Text)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Vote(db.Model):
    __tablename__ = "votes"

    id = db.Column(db.Integer, primary_key=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey("citizens.id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    # Prevent double voting: one vote per citizen per election
    __table_args__ = (db.UniqueConstraint("citizen_id", "election_id", name="unique_citizen_election_vote"),)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(200), nullable=False)
    level = db.Column(db.String(200))  # ward, municipality, district, province, federal
    description = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(300))
    status = db.Column(db.String(50), default="received")  # received, investigating, resolved
    case_token = db.Column(db.String(64), unique=True)  # anonymous tracking token
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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
    status = db.Column(db.String(50), default="Pending")  # Pending, Processing, Approved, Rejected
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

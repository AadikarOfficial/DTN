import sys
import os

# Auto-inject venv packages if available (allows running without manual venv activation)
_venv_candidates = [
    os.path.join(os.path.dirname(__file__), 'venv', 'lib'),
    '/home/claude/DTN_fixed/venv/lib',
]
for _venv in _venv_candidates:
    if os.path.isdir(_venv):
        for _sub in os.listdir(_venv):
            _sp = os.path.join(_venv, _sub, 'site-packages')
            if os.path.isdir(_sp) and _sp not in sys.path:
                sys.path.insert(0, _sp)
        break

from flask import Flask, jsonify
from config import Config
from database import db
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from routes.auth import auth_bp
from routes.citizen import citizen_bp
from routes.voting import voting_bp
from routes.whistleblower import whistle_bp
from routes.services import services_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    jwt = JWTManager(app)

    # JWT error handlers
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({"error": "Authorization token required"}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({"error": "Token has expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"error": "Invalid token"}), 401

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(citizen_bp)
    app.register_blueprint(voting_bp)
    app.register_blueprint(whistle_bp)
    app.register_blueprint(services_bp)

    # Health check
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "Nepal Digital Government API"})

    # Serve frontend
    @app.route("/")
    @app.route("/index.html")
    def index():
        from flask import render_template
        return render_template("index.html")

    # Create tables
    with app.app_context():
        db.create_all()
        _seed_initial_data()

    return app


def _seed_initial_data():
    """Seed initial services and sample election data if empty."""
    from models import Service, Election, Candidate
    from datetime import datetime, timedelta

    if Service.query.count() == 0:
        services = [
            Service(name="Passport Application", description="Apply for a new passport", department="Department of Passports"),
            Service(name="Citizenship Certificate", description="Apply or renew citizenship certificate", department="District Administration Office"),
            Service(name="Driving License", description="Apply for driving license", department="Department of Transport Management"),
            Service(name="Birth Certificate", description="Register birth and obtain certificate", department="Municipal Office"),
            Service(name="Land Registration", description="Register or transfer land ownership", department="Land Revenue Office"),
            Service(name="Tax Filing", description="File income tax returns online", department="Inland Revenue Department"),
            Service(name="Loksewa Exam Registration", description="Register for civil service examinations", department="Public Service Commission"),
            Service(name="Business Registration", description="Register a new business or company", department="Office of Company Registrar"),
        ]
        db.session.add_all(services)

    if Election.query.count() == 0:
        election = Election(
            name="Kathmandu Metropolitan City Mayor Election 2081",
            election_type="local",
            constituency="Kathmandu Metropolitan City",
            province="Bagmati",
            status="open",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(election)
        db.session.flush()

        candidates = [
            Candidate(name="Balen Shah", party="Independent", symbol="House", election_id=election.id),
            Candidate(name="Sirjanaa Singh", party="CPN-UML", symbol="Sun", election_id=election.id),
            Candidate(name="Sita Pradhan", party="Nepali Congress", symbol="Tree", election_id=election.id),
        ]
        db.session.add_all(candidates)

    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

import sys, os

_venv = os.path.join(os.path.dirname(__file__), 'venv', 'lib')
if os.path.isdir(_venv):
    for _sub in os.listdir(_venv):
        _sp = os.path.join(_venv, _sub, 'site-packages')
        if os.path.isdir(_sp) and _sp not in sys.path:
            sys.path.insert(0, _sp)

from flask import Flask, jsonify, render_template
from config import Config
from database import db
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from routes.auth import auth_bp
from routes.citizen import citizen_bp
from routes.voting import voting_bp
from routes.whistleblower import whistle_bp
from routes.services import services_bp
from routes.admin import admin_bp
from routes.community import community_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    jwt = JWTManager(app)

    @jwt.unauthorized_loader
    def unauth(e): return jsonify({"error": "Authorization token required"}), 401
    @jwt.expired_token_loader
    def expired(h, d): return jsonify({"error": "Token has expired"}), 401
    @jwt.invalid_token_loader
    def invalid(e): return jsonify({"error": "Invalid token"}), 401

    for bp in [auth_bp, citizen_bp, voting_bp, whistle_bp, services_bp, admin_bp, community_bp]:
        app.register_blueprint(bp)

    @app.route("/api/health")
    def health(): return jsonify({"status": "ok"})

    @app.route("/")
    @app.route("/index.html")
    def index(): return render_template("index.html")

    @app.route("/admin")
    @app.route("/admin.html")
    def admin_page(): return render_template("admin.html")

    with app.app_context():
        db.create_all()
        _seed()

    return app


def _seed():
    from models import Service, Citizen
    import bcrypt

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

    if not Citizen.query.filter_by(citizenship_number="ADMIN-001").first():
        pw = bcrypt.hashpw(b"admin1234", bcrypt.gensalt(rounds=12))
        admin = Citizen(
            full_name_nep="प्रशासक", full_name_eng="System Administrator",
            dob="1980-01-01", gender="Other",
            province="Bagmati", district="Kathmandu",
            municipality="Kathmandu Metropolitan City", ward=1,
            citizenship_number="ADMIN-001", issued_district="Kathmandu",
            mobile="9800000000", password_hash=pw,
            role="admin", status="approved", is_active=True
        )
        db.session.add(admin)

    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

# 🇳🇵 Nepal Digital Government Platform (DTN)

A secure-by-design government digital platform for Nepal covering citizen registration, digital voting, public services, and anonymous whistleblowing.

## 🚀 Quick Start

### Requirements
- Python 3.10+
- pip

### Setup & Run

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install flask flask-sqlalchemy flask-jwt-extended flask-cors bcrypt python-dotenv

# 3. Copy and configure environment
cp .env.example .env
# Edit .env and set strong SECRET_KEY and JWT_SECRET_KEY

# 4. Run the backend
python app.py
```

The API starts at: **http://localhost:5000**

### Test the API

```bash
# Health check
curl http://localhost:5000/api/health

# Register a citizen
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"full_name_eng":"Ram Thapa","full_name_nep":"राम थापा","dob":"1990-01-15","gender":"male","province":"Bagmati","district":"Kathmandu","municipality":"KMC","ward":10,"citizenship_number":"12-34-56789","issued_district":"Kathmandu","mobile":"9841234567","password":"SecurePass123"}'

# Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"citizenship_number":"12-34-56789","password":"SecurePass123"}'

# List services (no auth needed)
curl http://localhost:5000/api/services

# Submit anonymous report
curl -X POST http://localhost:5000/api/report \
  -F "category=Corruption" \
  -F "level=municipal" \
  -F "description=Official demanded bribe for passport renewal at ward office"
```

## 📁 Project Structure

```
nepal_digital_gov/
├── app.py              # Flask app factory, blueprints, seeding
├── config.py           # Config with .env support
├── database.py         # SQLAlchemy instance
├── models.py           # All DB models (Citizen, Election, Vote, Report, Service)
├── requirements.txt
├── .env                # Your secrets (DO NOT COMMIT)
├── .env.example        # Template
├── routes/
│   ├── auth.py         # Login, refresh token, /me endpoint
│   ├── citizen.py      # Register, view/list citizens
│   ├── voting.py       # Elections, candidates, cast vote, results
│   ├── whistleblower.py# Anonymous report submission + tracking
│   └── services.py     # Government services + applications
├── uploads/            # Uploaded files (gitignored)
└── templates/
    └── index.html      # Full frontend UI
```

## 🔐 Security Features

| Feature | Implementation |
|---------|----------------|
| Password hashing | bcrypt (12 rounds) |
| Authentication | JWT (30min access + 24h refresh tokens) |
| Double vote prevention | DB UniqueConstraint on (citizen_id, election_id) |
| Anonymous reporting | Random 64-char case tokens, no identity stored |
| File upload security | Extension whitelist, filename hashing, path traversal prevention |
| Input validation | Required field checks, format validation |
| Role-based access | citizen / officer / admin roles on all protected endpoints |

## 🌐 API Endpoints

### Auth
- `POST /api/register` — Register new citizen
- `POST /api/login` — Login, returns JWT tokens
- `POST /api/refresh` — Refresh access token
- `GET /api/me` — Get current user profile (auth required)

### Citizens (auth required)
- `GET /api/citizens/<id>` — View citizen profile
- `GET /api/citizens` — List all (admin only)

### Voting (auth required)
- `GET /api/elections` — List elections
- `GET /api/elections/<id>` — Election + candidates
- `POST /api/vote` — Cast vote (one per citizen per election)
- `GET /api/elections/<id>/results` — Results (only after closed)
- `POST /api/elections` — Create election (admin only)

### Services
- `GET /api/services` — List all services
- `POST /api/services/apply` — Apply (auth required)
- `GET /api/services/my-applications` — My applications (auth required)
- `PUT /api/services/applications/<id>` — Update status (officer/admin)

### Whistleblower (anonymous)
- `POST /api/report` — Submit anonymous report
- `GET /api/report/track?token=<token>` — Track report by token

### Health
- `GET /api/health` — Service health check

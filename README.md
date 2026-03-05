# Sarkar Digital — Nepal e-Government Platform

A secure-by-design digital government platform. Built for the BCS Hackathon.

## Setup

```bash
cd DTN
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # Edit SECRET_KEY and JWT_SECRET_KEY
python app.py
```

Open http://localhost:5000 (citizen portal) and http://localhost:5000/admin (admin panel).

## Default Admin Credentials
- Citizenship Number: `ADMIN-001`
- Password: `admin1234`

## Architecture

- **Backend**: Flask + SQLAlchemy + JWT + bcrypt
- **Database**: SQLite (dev) — swap for PostgreSQL in production
- **Auth**: JWT access tokens (30 min) + refresh tokens (24 hr)
- **Roles**: citizen / officer / admin

## Key Security Features

1. **bcrypt password hashing** (12 rounds)
2. **JWT authentication** on all protected endpoints
3. **Role-based access control** (citizen/officer/admin)
4. **Admin approval flow** — citizens cannot vote/apply until approved
5. **District-based voting eligibility** — voters can only vote in their registered district's elections
6. **Double-vote prevention** — DB-level unique constraint per (citizen, election)
7. **Anonymous whistleblower** — 64-char hex tokens, no identity stored, IP not logged
8. **File upload security** — extension whitelist + filename hashing (SHA-256)
9. **SQL injection protection** — ORM parameterised queries throughout
10. **Input validation** — server-side validation on all endpoints

## Features

### Citizen Portal (`/`)
- Register with citizenship details (pending admin approval)
- Login with citizenship number + password
- Browse and apply for 8 government services
- Vote in open elections (district eligibility enforced)
- Community board — post ideas, feedback, complaints
- Anonymous whistleblower report submission + tracking
- Personal dashboard with application status and voting history

### Admin Panel (`/admin`)
- Real-time stats dashboard
- Citizen approval queue — approve/reject registrations
- Role management — create custom roles with permissions
- Government position management — assign positions to citizens
- Election management — create elections with Online/Paper/Hybrid modes
- Candidate pool — import 50,000 candidates from CSV, filter and add to elections
- District-based voter eligibility on elections
- Hybrid elections — enter paper results, compare with online votes for discrepancy detection
- Whistleblower report management — update status, add admin notes
- Service application management — approve/reject citizen applications
- Community moderation — pin, hide, delete posts

## Voting Modes
- **Online**: Citizens vote via the portal; eligibility by registered district
- **Paper**: Voting done at polling stations; admin enters results
- **Hybrid**: Both online + paper; results compared for discrepancy detection (paper takes precedence)

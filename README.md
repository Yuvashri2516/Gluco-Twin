# 🩺 GlucoTwin

**An Intelligent Predictive Digital Twin for Proactive Glucose-Risk Monitoring**

> ⚠️ This is a **hackathon prototype** using **synthetic data only**.
> It is **not clinically validated** and must not be used for real patient care.

---

## What Is GlucoTwin?

GlucoTwin maintains a virtual "digital twin" of each patient that evolves
as new glucose, heart-rate, and HRV readings arrive. It estimates future
glucose-spike risk, explains its predictions, generates alerts, and provides
a doctor-facing dashboard.

## Tech Stack

| Layer    | Technology                                     |
|----------|-------------------------------------------------|
| Frontend | React · Vite · Recharts · CSS                  |
| Backend  | Python · FastAPI · Uvicorn                      |
| ML       | scikit-learn · NumPy · Pandas                   |
| Database | SQLite (via SQLAlchemy ORM)                     |

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

The server seeds 5 synthetic patients with 72 hours of readings on first launch.

**Verify it works:**
- Health check: [http://localhost:8000/health](http://localhost:8000/health)
- API docs:     [http://localhost:8000/docs](http://localhost:8000/docs)
- Patients:     [http://localhost:8000/api/patients/](http://localhost:8000/api/patients/)

### 2. Frontend (Phase 2)

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
Gluco-Twin/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── database.py      # SQLite + SQLAlchemy setup
│   │   ├── models.py        # ORM models
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── seed.py          # Synthetic data generator
│   │   └── routers/
│   │       ├── patients.py  # Patient CRUD endpoints
│   │       └── readings.py  # Glucose & vitals endpoints
│   └── requirements.txt
├── frontend/                # React + Vite (Phase 2)
└── README.md
```

## API Endpoints (Phase 1)

| Method | Path                              | Description                |
|--------|-----------------------------------|----------------------------|
| GET    | `/health`                         | Server health check        |
| GET    | `/api/patients/`                  | List all patients          |
| GET    | `/api/patients/{id}`              | Get one patient            |
| GET    | `/api/readings/glucose/{id}?hours=24` | Glucose time-series    |
| GET    | `/api/readings/vitals/{id}?hours=24`  | HR + HRV time-series   |

## Licence

MIT — see [LICENSE](LICENSE) for details.

# BiasX-Ray

BiasX-Ray is an AI fairness auditing platform that detects hidden discrimination in machine learning systems.

## Features

- CSV upload with preview
- Bias scan across sensitive and intersectional groups
- Fairness metrics: approval rate gap, disparate impact, fairness score
- What-if simulator for profile changes
- Gemini-powered explanations and recommendations
- Downloadable JSON report from latest scan

## Project Structure

- `frontend/` Next.js 14 + TypeScript + Tailwind + Recharts
- `backend/` FastAPI service with modular routes and services
- `ml-engine/` Reusable fairness and simulation logic
- `datasets/` Sample datasets
- `infra/` Dockerfiles

## Environment Setup

### Backend

Create or edit `backend/.env`:

```env
GEMINI_API_KEY=
GOOGLE_CLOUD_PROJECT=
BUCKET_NAME=
```

### Frontend

Create or edit `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Local Development

## 1) Backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`

### New endpoints

- `POST /analyze` - run full agentic audit orchestration (data audit, bias hunt, explainability, remediation)

The backend now auto-detects a target column on upload and will kick off a background training job (XGBoost primary, RandomForest fallback). Trained model artifacts are stored under `backend/models/`.

## 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:3000`

## Backend Routes

- `GET /health`
- `POST /upload`
- `POST /scan`
- `POST /simulate`
- `POST /explain`
- `GET /report`

## Docker Compose

From repository root:

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

## Deploy to Google Cloud Run (Quick Path)

### Backend

```bash
gcloud builds submit --tag gcr.io/<PROJECT_ID>/biasxray-backend -f infra/Dockerfile.backend .
gcloud run deploy biasxray-backend \
  --image gcr.io/<PROJECT_ID>/biasxray-backend \
  --platform managed \
  --region <REGION> \
  --allow-unauthenticated
```

### Frontend

Set `NEXT_PUBLIC_API_URL` to deployed backend URL before build.

```bash
gcloud builds submit --tag gcr.io/<PROJECT_ID>/biasxray-frontend -f infra/Dockerfile.frontend .
gcloud run deploy biasxray-frontend \
  --image gcr.io/<PROJECT_ID>/biasxray-frontend \
  --platform managed \
  --region <REGION> \
  --allow-unauthenticated
```

## Notes

- The latest uploaded dataset path and latest scan report are kept in backend runtime memory.
- If Gemini key is missing, explanation API returns a safe local fallback explanation.
- Sample biased dataset is available at `datasets/sample_loan_data.csv`.

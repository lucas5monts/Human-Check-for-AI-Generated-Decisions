# Second Look 

Second Look is a small full-stack app for reviewing AI-assisted hiring or ATS decision packets.

It does not decide whether an applicant should be hired. It scores how risky it is to trust an automated decision without human review..

## What It Does

- Accepts structured JSON applicant decision packets
- Scores each packet with a rule-based compliance engine
- Flags missing explanations, weak evidence, keyword overreliance, low data quality, and transparency issues
- Returns a `green`, `yellow`, or `red` risk level
- Displays results in a modern review dashboard

## Stack

- Frontend: Astro, React, CSS
- Backend: FastAPI, Pydantic, Python
- Optional batch processing: Python queue processor
- Deployment support: Docker

## Project Structure

```text
backend/
  incoming/              sample/test packets
  main.py                FastAPI routes
  scorer.py              scoring engine
  queue_processor.py     optional batch processor
  requirements.txt

frontend/
  src/components/        React dashboard components
  src/lib/api.js         frontend API URL helper
  src/pages/index.astro
  src/styles/styles.css
  package.json
```

## Run Locally

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend URL:

```text
http://localhost:8000
```

API docs:

```text
http://localhost:8000/api/docs
```

### Frontend

```bash
cd frontend
npm install
PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Frontend URL:

```text
http://localhost:4321
```

If the frontend starts on another port, use the URL printed by Astro.

## API Routes

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api` | Health check |
| `POST` | `/api/audit` | Score one applicant packet |
| `GET` | `/api/test-data` | Score all JSON files in `backend/incoming/` |
| `GET` | `/api/docs` | FastAPI docs |

## Risk Levels

| Score | Level | Meaning |
|---|---|---|
| `0-29` | Green | Low risk |
| `30-59` | Yellow | Needs attention |
| `60-100` | Red | Human review required |

## Test Data

Add JSON files to:

```text
backend/incoming/
```

Then start the backend and frontend. The dashboard loads scored packets from:

```text
/api/test-data
```

## Optional Queue Processor

Run this from `backend/`:

```bash
python queue_processor.py
```

It reads files from `incoming/`, scores them, writes results, updates a CSV summary, and moves files into `processed/` or `failed/`.

## Docker

Backend:

```bash
cd backend
docker build -t second-look-backend .
docker run -p 8000:8000 second-look-backend
```

Frontend:

```bash
cd frontend
docker build -t second-look-frontend .
docker run -p 80:80 second-look-frontend
```

## Notes

- The scorer is rule-based, not machine-learning based.
- Input packets must be structured JSON.
- The app estimates review risk; it does not validate the correctness of the hiring decision.
- Set `PUBLIC_API_BASE_URL` when the frontend should call a specific backend URL.

## License

GPL-3.0

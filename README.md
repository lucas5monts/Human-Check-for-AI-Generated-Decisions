# Second Look ATS Auditing Tool

Second Look is a full-stack web application for auditing automated hiring or ATS decision packets. The tool helps reviewers identify whether an applicant decision has enough supporting evidence, transparency, and data quality to be trusted without additional human review.

The application takes structured JSON decision packets, scores them using a rule-based compliance engine, and displays each applicant's risk level, risk score, and triggered audit rules in a simple dashboard.

## What This Project Does

Second Look does not decide whether an applicant should be hired or rejected. Instead, it evaluates the risk of trusting an automated hiring decision.

The system checks for issues such as:

- Missing explanations
- Missing documentation
- Weak or missing reason codes
- Low resume parsing confidence
- Incomplete applicant data
- Overreliance on keyword matching
- Lack of semantic matching
- Possible proxy-risk terms
- Low decision observability
- Limited vendor transparency
- Contradictory decision signals

Each packet receives:

- A risk score from 0 to 100
- A risk level: `green`, `yellow`, or `red`
- A flag for whether human review is required
- A list of triggered rules explaining why the score was assigned

## Tech Stack

### Frontend

- Astro
- React
- JavaScript
- CSS

### Backend

- Python
- FastAPI
- Pydantic
- Uvicorn

### Deployment Support

- Docker
- Caddy for serving the built frontend
- FastAPI backend container

## Project Structure

second-look/
  frontend/
    public/
    src/
      components/
        Accordion.jsx
        Applicant.jsx
        Header.jsx
      pages/
        index.astro
      styles/
        styles.css
    astro.config.mjs
    package.json
    Dockerfile

  backend/
    incoming/
    main.py
    scorer.py
    queue_processor.py
    jsonInputExample1.json
    requirements.txt
    Dockerfile

  README.md

## Backend Overview

The backend contains the scoring logic and API routes.

### Main files

`backend/main.py`

Creates the FastAPI app and exposes the API endpoints.

`backend/scorer.py`

Contains the rule-based compliance scoring engine.

`backend/queue_processor.py`

Optional batch-processing script that can read JSON files from `incoming/`, score them, save results, and move processed files.

## API Endpoints

### Health Check

GET /api

Returns a simple test response.

### Score One Applicant Packet

POST /api/audit

Accepts one JSON applicant decision packet and returns the scoring result.

### Load Test Data

GET /api/test-data

Reads JSON files from the backend `incoming/` folder, scores them in memory, and returns the results to the frontend.

### API Docs

GET /api/docs

Opens the interactive FastAPI Swagger documentation.

## Example Input

{
  "packet_id": "PKT-1007",
  "source_system": "ThirdPartyATS-X",
  "domain": "hiring",
  "applicant_id": "C102",
  "decision_packet": {
    "final_recommendation": "reject",
    "reason_codes": ["missing_required_skills", "low_match_score"],
    "explanation_text": "Applicant did not meet required skill criteria.",
    "explanation_present": true,
    "documentation_present": true
  },
  "applicant_data": {
    "resume_parse_confidence": 0.68,
    "missing_fields": ["employment_gap_reason"],
    "data_completeness_score": 0.74,
    "file_format": "pdf"
  },
  "keyword_assessment": {
    "keyword_score": 0.35,
    "keywords_matched": ["python", "sql"],
    "keywords_missing": ["pandas", "machine learning"],
    "match_count": 2,
    "total_keywords_considered": 4,
    "possible_proxy_terms_detected": false,
    "overreliance_risk": true,
    "semantic_match_available": false,
    "keyword_rules_transparent": false
  },
  "oversight_features": {
    "decision_observability_score": 0.45,
    "contradiction_flag": false,
    "insufficient_explanation_flag": true,
    "vendor_transparency_limited": true
  }
}

## Example Output

{
  "packet_id": "PKT-1007",
  "applicant_id": "C102",
  "risk_score": 100,
  "risk_level": "red",
  "human_review_required": true,
  "triggered_rules": [
    {
      "name": "low_resume_parse_confidence",
      "points": 20,
      "reason": "Resume parse confidence is low (0.68)."
    },
    {
      "name": "low_data_completeness",
      "points": 15,
      "reason": "Data completeness score is low (0.74)."
    }
  ]
}

## Getting Started

### Prerequisites

Make sure you have the following installed:

- Python 3.11+
- Node.js 22.12+
- npm

## Run the Backend Locally

From the backend folder:

cd backend
python -m venv venv
source venv/bin/activate

On Windows:

cd backend
python -m venv venv
venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Start the FastAPI server:

uvicorn main:app --reload --host 0.0.0.0 --port 8000

The backend should now be running at:

http://localhost:8000

FastAPI docs:

http://localhost:8000/api/docs

## Run the Frontend Locally

From the frontend folder:

cd frontend
npm install
npm run dev

The frontend should now be running at:

http://localhost:4321

## Connecting Frontend and Backend Locally

The backend allows requests from:

http://localhost:4321
http://127.0.0.1:4321
http://localhost:80
http://127.0.0.1:80

For local development, make sure the frontend is calling your local backend:

http://localhost:8000/api/test-data

or

http://localhost:8000/api/audit

If the frontend is still pointing to the deployed API URL, update the fetch URL in:

frontend/src/pages/index.astro
frontend/src/components/Header.jsx

## Running with Docker

### Backend Docker Build

cd backend
docker build -t second-look-backend .
docker run -p 8000:8000 second-look-backend

### Frontend Docker Build

cd frontend
docker build -t second-look-frontend .
docker run -p 80:80 second-look-frontend

The frontend container serves the built Astro site through Caddy.

## Using Test Data

To test the app with sample applicant packets:

1. Add one or more `.json` files to:

backend/incoming/

2. Start the backend.

3. Visit the frontend.

4. The frontend will request test data from:

/api/test-data

5. The dashboard will display scored applicant packets.

## Optional Queue Processor

The backend includes a queue processor for batch-style processing.

Run it from the backend folder:

python queue_processor.py

This script:

1. Reads JSON files from `incoming/`
2. Scores each packet
3. Saves result JSON files
4. Appends a summary CSV row
5. Moves successful files to `processed/`
6. Moves failed files to `failed/`

## Risk Levels

| Score Range | Risk Level | Meaning |
|---|---|---|
| 0-29 | Green | Low risk |
| 30-59 | Yellow | Moderate risk |
| 60-100 | Red | High risk; human review required |

## Current Limitations

- The scoring engine is rule-based, not machine-learning based.
- The tool depends on structured JSON input.
- It does not verify whether the hiring decision is correct.
- It only estimates whether the available evidence is strong enough to trust.
- The frontend may need its API URLs updated depending on local or deployed setup.

## Future Improvements

Possible next steps:

- Add authentication for reviewers
- Add database storage for applicant audit history
- Add file upload support for multiple packets
- Add filtering by risk level
- Add reviewer notes
- Add export options for CSV or PDF reports
- Improve UI styling and dashboard layout
- Add environment variables for API URLs instead of hardcoded fetch paths

## License

This project is licensed under the GPL-3.0 License.
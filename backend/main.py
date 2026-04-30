from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from scorer import ComplianceScoringEngine, RiskEvaluationResult, load_json_file, result_to_dict

engine = ComplianceScoringEngine()
BASE_DIR = Path(__file__).resolve().parent
INCOMING_DIR = BASE_DIR / "incoming"

app = FastAPI(
    title="Resume Audit API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc"
)

ALLOWED_ORIGINS = [
    "https://secondlook.venykrid.com"
]
LOCAL_ORIGIN_REGEX = r"^http://(localhost|127\.0\.0\.1):\d+$"
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=LOCAL_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DecisionPacket(BaseModel):
    final_recommendation: Optional[str] = "unknown"
    reason_codes: Optional[List[str]] = Field(default_factory=list)
    explanation_present: Optional[bool] = False
    documentation_present: Optional[bool] = False

class ApplicantData(BaseModel):
    resume_parse_confidence: Optional[float] = None
    missing_fields: Optional[List[str]] = Field(default_factory=list)
    data_completeness_score: Optional[float] = None

class KeywordAssessment(BaseModel):
    keyword_score: Optional[float] = None
    possible_proxy_terms_detected: Optional[bool] = False
    overreliance_risk: Optional[bool] = False
    semantic_match_available: Optional[bool] = False
    keyword_rules_transparent: Optional[bool] = True

class OversightFeatures(BaseModel):
    decision_observability_score: Optional[float] = None
    contradiction_flag: Optional[bool] = False
    insufficient_explanation_flag: Optional[bool] = False
    vendor_transparency_limited: Optional[bool] = False

class AuditPayload(BaseModel):
    packet_id: Optional[str] = "UNKNOWN_PACKET"
    applicant_id: Optional[str] = "UNKNOWN_APPLICANT"
    decision_packet: Optional[DecisionPacket] = Field(default_factory=DecisionPacket)
    applicant_data: Optional[ApplicantData] = Field(default_factory=ApplicantData)
    keyword_assessment: Optional[KeywordAssessment] = Field(default_factory=KeywordAssessment)
    oversight_features: Optional[OversightFeatures] = Field(default_factory=OversightFeatures)

@app.get("/api")
async def root():
    return {"message": "Hello World"}

@app.post("/api/audit", response_model=RiskEvaluationResult)
async def evaluate_resume_packet(payload: AuditPayload):
    packet_dict = payload.model_dump()
    return engine.evaluate_packet(packet_dict)

@app.get("/api/test-data")
async def fetch_in_memory_test_data():
    if not INCOMING_DIR.exists():
        return {"status": "success", "count": 0, "data": []}

    json_files = sorted(INCOMING_DIR.glob("*.json"))
    results = []

    for file_path in json_files:
        try:
            packet = load_json_file(file_path)
            evaluation = engine.evaluate_packet(packet)
            evaluation_dict = result_to_dict(evaluation)
            evaluation_dict["source_file"] = file_path.name
            results.append(evaluation_dict)
        except Exception as e:
            print(f"Skipping {file_path.name} due to error: {e}")

    return {
        "status": "success",
        "count": len(results),
        "data": results
    }

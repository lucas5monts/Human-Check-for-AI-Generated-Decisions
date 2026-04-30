# Main API source
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from scorer import *

engine = ComplianceScoringEngine()

app = FastAPI(
    title="Resume Audit API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc"
)

# Origin allow list for API calls
origins = [
    "http://localhost:4321",
    "http://127.0.0.1:4321",
    "http://localhost:80",
    "http://127.0.0.1:80",
    "https://secondlook.venykrid.com"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models based on scorer.py safe_get paths ---

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
    """
    Receives an applicant packet from Astro, evaluates it through the scoring engine,
    and returns the risk evaluation result.
    """
    # Dump the model
    packet_dict = payload.model_dump()
    
    # Run the engine
    result = engine.evaluate_packet(packet_dict)
    
    # Return the dataclass directly; FastAPI will convert it to JSON
    return result

INCOMING_DIR = Path("incoming")
@app.get("/api/test-data")
async def fetch_in_memory_test_data():
    """
    Reads all JSON files in incoming/, scores them in memory, 
    and returns the results without mutating the file system.
    """
    if not INCOMING_DIR.exists():
        return {"status": "success", "count": 0, "data": []}

    # Find all JSON files
    json_files = sorted(INCOMING_DIR.glob("*.json"))
    results = []

    for file_path in json_files:
        try:
            # 1. Load the raw JSON from disk
            packet = load_json_file(str(file_path))
            
            # 2. Score it in memory
            evaluation = engine.evaluate_packet(packet)
            
            # 3. Attach the filename so the frontend knows which is which
            # We convert the dataclass to a dict so we can inject the filename
            evaluation_dict = evaluation.__dict__.copy()
            evaluation_dict["source_file"] = file_path.name
            
            results.append(evaluation_dict)
            
        except Exception as e:
            # If one file is corrupted, print it but don't crash the whole API
            print(f"Skipping {file_path.name} due to error: {e}")

    # Return the aggregated data
    return {
        "status": "success",
        "count": len(results),
        "data": results
    }
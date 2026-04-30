The following document describes how queue_processor.py automates .json file input into scorer.py.


Instead of manually passing files into scorer.py one-by-one, the
queue processor:


- Reads incoming applicant JSON files
- Sends them to the scoring engine
- Saves structured results
- Updates a dashboard summary
- Organizes processed and failed files


This allows SecondLook to operate as a scalable middleware layer
between third-party HR systems and human reviewers.


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


SYSTEM ROLE (IN ARCHITECTURE)


Resume / Applicant Data
↓
Third-Party HR Software (Black Box)
↓
JSON Decision Packets
↓
QUEUE PROCESSOR (this script)
↓
ComplianceScoringEngine (scorer.py)
↓
Risk Results + Flags
↓
Dashboard / Human Review


---------------------------------------------------------------------


FOLDER STRUCTURE


project/
├── scorer.py
├── queue_processor.py
├── incoming/
├── processed/
├── failed/
├── results/
└── dashboard_summary.csv


---------------------------------------------------------------------


FOLDER DESCRIPTIONS


incoming/
- Drop new applicant JSON files here
- These files will be picked up and processed automatically


processed/
- Successfully processed files are moved here


failed/
- Files that could not be processed (invalid JSON, missing fields, etc.)


results/
- Contains output JSON files with scoring results per applicant


dashboard_summary.csv
- Aggregated table used by dashboard or frontend


---------------------------------------------------------------------


HOW IT WORKS


1. The script scans the "incoming/" folder for .json files


2. For each file:
- Load JSON packet
- Send to ComplianceScoringEngine (scorer.py)
- Compute risk score and flags


3. Output is generated:
- A result JSON file is saved in "results/"
- A summary row is appended to dashboard_summary.csv


4. File is moved:
- Success → "processed/"
- Failure → "failed/"


---------------------------------------------------------------------


OUTPUT FILES


Per Applicant Result (JSON):


results/applicant_001_result.json


Contains:
- packet_id
- applicant_id
- risk_score
- risk_level (green / yellow / red)
- human_review_required (True/False)
- triggered_rules (list of rule explanations)


---------------------------------------------------------------------


Dashboard Summary (CSV):


dashboard_summary.csv


Columns:
- source_file
- packet_id
- applicant_id
- risk_score
- risk_level
- human_review_required
- top_reasons


Example Row:


applicant_001.json,PKT-001,C001,65,red,True,"missing_explanation (20); low_parse_confidence (20); keyword_overreliance (20)"


---------------------------------------------------------------------


RISK LEVEL MEANING


Green (0–29)
- Safe to proceed
- No immediate human review required


Yellow (30–59)
- Moderate risk
- May require monitoring or optional review


Red (60+)
- High risk
- Human review REQUIRED


---------------------------------------------------------------------


RUNNING THE SCRIPT


Step 1:
Place JSON files into:
incoming/


Step 2:
Run the script:


python queue_processor.py


Step 3:
Check outputs:
- results/ folder
- dashboard_summary.csv
- processed/ folder


---------------------------------------------------------------------


CONTINUOUS MODE (OPTIONAL)


To continuously monitor the incoming folder:


In queue_processor.py, set:


CONTINUOUS_MODE = True


Then run:


python queue_processor.py


The script will:
- check for new files every few seconds
- process them automatically


Stop with:
Ctrl + C


---------------------------------------------------------------------


QUEUE ORDERING


Files are processed in sorted filename order.


Recommended naming format:


YYYYMMDD_###_applicant.json


Example:
20260410_001_applicant.json
20260410_002_applicant.json


This ensures predictable queue behavior.


---------------------------------------------------------------------


ERROR HANDLING


If a file fails processing:
- It is moved to "failed/"
- The error is printed to console


Common failure reasons:
- Invalid JSON format
- Missing required fields
- Unexpected structure


---------------------------------------------------------------------


DESIGN PRINCIPLES


1. Separation of Concerns
- queue_processor handles file flow
- scorer.py handles scoring logic


2. Transparency
- Every decision produces explainable outputs


3. Scalability
- Designed to handle batches or continuous input


4. Non-Intrusive
- Does NOT modify scorer.py
- Acts as a wrapper layer


---------------------------------------------------------------------


FUTURE IMPROVEMENTS (NOT IN PHASE 1)


- Duplicate packet detection
- Error logging file (queue.log)
- Dashboard JSON output (grouped by risk level)
- Real-time frontend integration
- API-based ingestion instead of file system
- Parallel processing for large batches


---------------------------------------------------------------------


SUMMARY


The queue processor transforms SecondLook from a manual tool into
an automated pipeline.


It enables:
- Batch processing
- Consistent scoring
- Dashboard-ready outputs
- Human-in-the-loop review at scale


This is a critical component of the SecondLook system.


---------------------------------------------------------------------
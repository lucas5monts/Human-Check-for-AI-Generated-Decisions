The following document describes how scorer.py grades documents. This is helpful for human developers to grade .json input to check their own scores against output of scorer.py .


This scoring system evaluates whether an AI-generated decision is sufficiently reliable, transparent, and supported to proceed without human review.
Higher scores indicate greater risk and a stronger need for human oversight.
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
Risk Bands
* 0–29 → Green (Safe/Low risk)
* 30–59 →Yellow (Moderate Risk)
* 60+ →Red (Human Review Required)
________________


Scoring Rules
Transparency / Explanation
* +20 → No explanation provided
* +15 → Explanation marked insufficient
* +15 → Rejection with no reason codes
* +10 → Missing documentation
* +15 → Vendor transparency limited
* +20 → Low decision observability (< 0.60)
________________


Data Quality / Parsing
* +20 → Resume parse confidence < 0.75
* +10–15 → Missing applicant fields
   * 1–2 fields → +10
   * 3+ fields → +15
* +15 → Data completeness < 0.80
________________


Keyword Risks
* +20 → Keyword overreliance (exact match issue)
* +10 → No semantic matching available
* +10 → Keyword logic not transparent
* +25 → Possible proxy terms detected
* +10 → Low keyword score (< 0.40) in rejection case
________________


Decision Reliability / Logic
* +25 → Contradiction flag (data conflicts with decision)
* +10 → Rejection with weak supporting evidence
________________


Special Rule
Negative decisions get extra scrutiny
If:
* rejection AND
* weak support, includes:
   * Missing explanation
   * Missing reason codes
   * Limited vendor transparency
   * Insufficient explanation flag
→ +10 extra points
________________


Examples


Example 1:


If a packet has:
* No explanation (+20)
* Low parse confidence (+20)
* Keyword overreliance (+20)


Total score = 60 → Red (Human Review Required)








Example 2: 

If a packet has:
* Resume parse confidence = .6 (+20)


Total score = 20 → Green (low risk)


Example 3: 


If a packet has: 
* Keyword overreliance [exact match] (+20)
* Three (3) missing applicant fields (+15)
* Vendor transparency limited (+15)


Total score = 50 → Yellow (Moderate Risk)
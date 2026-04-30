import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


# -----------------------------
# Data classes for structured results
# -----------------------------

@dataclass
class TriggeredRule:
    """
    Represents one rule that fired during evaluation.
    """
    name: str
    points: int
    reason: str


@dataclass
class RiskEvaluationResult:
    """
    Final result returned by the scoring engine.
    """
    packet_id: str
    applicant_id: str
    risk_score: int
    risk_level: str
    human_review_required: bool
    triggered_rules: List[TriggeredRule] = field(default_factory=list)


# -----------------------------
# Helper functions
# -----------------------------

def safe_get(data: Dict[str, Any], path: List[str], default=None):
    """
    Safely retrieves a nested value from a dictionary.

    Example:
        safe_get(packet, ["decision_packet", "final_recommendation"], "unknown")

    If any part of the path is missing, returns the default value.
    """
    current = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def clamp_score(score: int, minimum: int = 0, maximum: int = 100) -> int:
    """
    Ensures the risk score stays inside a predictable range.
    """
    return max(minimum, min(score, maximum))


# -----------------------------
# Core scoring engine
# -----------------------------

class ComplianceScoringEngine:
    """
    Phase 1 scoring engine.

    Design goal:
    - Easy to inspect
    - Easy to explain
    - Easy to change

    This engine does NOT try to prove that a hiring decision is wrong.
    It only estimates whether the available evidence is too weak or risky
    to trust without human review.
    """

    def __init__(self):
        # Risk thresholds for dashboard colors / actions
        self.green_max = 29
        self.yellow_max = 59
        # 60+ is red / human review required

    def evaluate_packet(self, packet: Dict[str, Any]) -> RiskEvaluationResult:
        """
        Main method that scores one decision packet.
        """
        packet_id = packet.get("packet_id", "UNKNOWN_PACKET")
        applicant_id = packet.get("applicant_id", "UNKNOWN_APPLICANT")

        score = 0
        triggered_rules: List[TriggeredRule] = []

        # -----------------------------
        # Extract key fields
        # -----------------------------
        final_recommendation = safe_get(
            packet, ["decision_packet", "final_recommendation"], "unknown"
        )
        reason_codes = safe_get(packet, ["decision_packet", "reason_codes"], [])
        explanation_present = safe_get(
            packet, ["decision_packet", "explanation_present"], False
        )
        documentation_present = safe_get(
            packet, ["decision_packet", "documentation_present"], False
        )

        resume_parse_confidence = safe_get(
            packet, ["applicant_data", "resume_parse_confidence"], None
        )
        missing_fields = safe_get(packet, ["applicant_data", "missing_fields"], [])
        data_completeness_score = safe_get(
            packet, ["applicant_data", "data_completeness_score"], None
        )

        keyword_score = safe_get(
            packet, ["keyword_assessment", "keyword_score"], None
        )
        possible_proxy_terms_detected = safe_get(
            packet, ["keyword_assessment", "possible_proxy_terms_detected"], False
        )
        overreliance_risk = safe_get(
            packet, ["keyword_assessment", "overreliance_risk"], False
        )
        semantic_match_available = safe_get(
            packet, ["keyword_assessment", "semantic_match_available"], False
        )
        keyword_rules_transparent = safe_get(
            packet, ["keyword_assessment", "keyword_rules_transparent"], True
        )

        decision_observability_score = safe_get(
            packet, ["oversight_features", "decision_observability_score"], None
        )
        contradiction_flag = safe_get(
            packet, ["oversight_features", "contradiction_flag"], False
        )
        insufficient_explanation_flag = safe_get(
            packet, ["oversight_features", "insufficient_explanation_flag"], False
        )
        vendor_transparency_limited = safe_get(
            packet, ["oversight_features", "vendor_transparency_limited"], False
        )

        # -----------------------------
        # Rule 1: Missing explanation
        # Why it matters:
        # If a system issues a negative decision without an explanation,
        # HR has less basis for trusting it.
        # -----------------------------
        if not explanation_present:
            score += 20
            triggered_rules.append(
                TriggeredRule(
                    name="missing_explanation",
                    points=20,
                    reason="No explanation was provided for the automated decision."
                )
            )

        # -----------------------------
        # Rule 2: Missing documentation
        # Why it matters:
        # If supporting documentation is missing, the decision is harder to audit.
        # -----------------------------
        if not documentation_present:
            score += 10
            triggered_rules.append(
                TriggeredRule(
                    name="missing_documentation",
                    points=10,
                    reason="Supporting documentation for the decision is missing."
                )
            )

        # -----------------------------
        # Rule 3: Weak or absent reason codes
        # Why it matters:
        # If there are no reason codes for a rejection, the rejection is less transparent.
        # -----------------------------
        if final_recommendation == "reject" and len(reason_codes) == 0:
            score += 15
            triggered_rules.append(
                TriggeredRule(
                    name="missing_reason_codes",
                    points=15,
                    reason="The applicant was rejected but no reason codes were provided."
                )
            )

        # -----------------------------
        # Rule 4: Low resume parse confidence
        # Why it matters:
        # If the resume may have been parsed incorrectly, any downstream scoring becomes less trustworthy.
        # -----------------------------
        if resume_parse_confidence is not None and resume_parse_confidence < 0.75:
            score += 20
            triggered_rules.append(
                TriggeredRule(
                    name="low_resume_parse_confidence",
                    points=20,
                    reason=f"Resume parse confidence is low ({resume_parse_confidence:.2f})."
                )
            )

        # -----------------------------
        # Rule 5: Missing applicant fields
        # Why it matters:
        # Incomplete applicant data may produce fragile or unfair screening results.
        # -----------------------------
        if len(missing_fields) >= 1:
            points = 10 if len(missing_fields) <= 2 else 15
            score += points
            triggered_rules.append(
                TriggeredRule(
                    name="missing_applicant_fields",
                    points=points,
                    reason=f"Applicant record has missing fields: {missing_fields}."
                )
            )

        # -----------------------------
        # Rule 6: Low completeness score
        # Why it matters:
        # If the packet is incomplete, trust in the final decision should decrease.
        # -----------------------------
        if data_completeness_score is not None and data_completeness_score < 0.80:
            score += 15
            triggered_rules.append(
                TriggeredRule(
                    name="low_data_completeness",
                    points=15,
                    reason=f"Data completeness score is low ({data_completeness_score:.2f})."
                )
            )

        # -----------------------------
        # Rule 7: Keyword overreliance
        # Why it matters:
        # Exact keyword matching can miss equivalent skills phrased differently.
        # -----------------------------
        if overreliance_risk:
            score += 20
            triggered_rules.append(
                TriggeredRule(
                    name="keyword_overreliance",
                    points=20,
                    reason="The decision may rely too heavily on exact keyword matching."
                )
            )

        # -----------------------------
        # Rule 8: No semantic matching support
        # Why it matters:
        # If semantic matching is unavailable, exact-match brittleness is more concerning.
        # -----------------------------
        if not semantic_match_available:
            score += 10
            triggered_rules.append(
                TriggeredRule(
                    name="no_semantic_matching",
                    points=10,
                    reason="Semantic matching is unavailable, increasing keyword brittleness risk."
                )
            )

        # -----------------------------
        # Rule 9: Keyword logic not transparent
        # Why it matters:
        # If HR cannot understand keyword logic, the result is harder to trust.
        # -----------------------------
        if not keyword_rules_transparent:
            score += 10
            triggered_rules.append(
                TriggeredRule(
                    name="keyword_logic_not_transparent",
                    points=10,
                    reason="Keyword scoring logic is not transparent."
                )
            )

        # -----------------------------
        # Rule 10: Proxy term concern
        # Why it matters:
        # Potential proxy terms may increase fairness or compliance risk.
        # -----------------------------
        if possible_proxy_terms_detected:
            score += 25
            triggered_rules.append(
                TriggeredRule(
                    name="possible_proxy_terms_detected",
                    points=25,
                    reason="Possible proxy-risk terms were detected in the keyword assessment."
                )
            )

        # -----------------------------
        # Rule 11: Low decision observability
        # Why it matters:
        # When using third-party systems, lack of observability should itself add risk.
        # -----------------------------
        if decision_observability_score is not None and decision_observability_score < 0.60:
            score += 20
            triggered_rules.append(
                TriggeredRule(
                    name="low_decision_observability",
                    points=20,
                    reason=f"Decision observability score is low ({decision_observability_score:.2f})."
                )
            )

        # -----------------------------
        # Rule 12: Explicit insufficient explanation flag
        # Why it matters:
        # This allows your upstream logic or a reviewer to mark the explanation as inadequate.
        # -----------------------------
        if insufficient_explanation_flag:
            score += 15
            triggered_rules.append(
                TriggeredRule(
                    name="insufficient_explanation_flag",
                    points=15,
                    reason="The available explanation was marked as insufficient."
                )
            )

        # -----------------------------
        # Rule 13: Limited vendor transparency
        # Why it matters:
        # Black-box vendor decisions deserve more caution in high-stakes settings.
        # -----------------------------
        if vendor_transparency_limited:
            score += 15
            triggered_rules.append(
                TriggeredRule(
                    name="vendor_transparency_limited",
                    points=15,
                    reason="The third-party system provides limited transparency."
                )
            )

        # -----------------------------
        # Rule 14: Contradictory case
        # Why it matters:
        # Contradictions suggest the decision should be reviewed by a human.
        # -----------------------------
        if contradiction_flag:
            score += 25
            triggered_rules.append(
                TriggeredRule(
                    name="contradiction_flag",
                    points=25,
                    reason="The packet contains contradictory signals that reduce trust in the automated outcome."
                )
            )

        # -----------------------------
        # Rule 15: Extra caution for negative decisions with weak support
        # Why it matters:
        # A rejection should be held to a higher standard than a positive or neutral recommendation.
        # -----------------------------
        weak_support = (
            not explanation_present
            or len(reason_codes) == 0
            or vendor_transparency_limited
            or insufficient_explanation_flag
        )

        if final_recommendation == "reject" and weak_support:
            score += 10
            triggered_rules.append(
                TriggeredRule(
                    name="negative_decision_with_weak_support",
                    points=10,
                    reason="A negative decision was issued despite weak supporting evidence."
                )
            )

        # Optional example use of keyword_score:
        # This rule does NOT assume a low keyword score is inherently bad.
        # It only adds risk when rejection + weak keyword support appear together.
        if final_recommendation == "reject" and keyword_score is not None and keyword_score < 0.40:
            score += 10
            triggered_rules.append(
                TriggeredRule(
                    name="low_keyword_support_for_rejection",
                    points=10,
                    reason=f"Keyword score is low ({keyword_score:.2f}) and contributed to a rejection scenario."
                )
            )

        # Keep score bounded
        score = clamp_score(score, 0, 100)

        # Convert numerical score to color/risk band
        if score <= self.green_max:
            risk_level = "green"
            human_review_required = False
        elif score <= self.yellow_max:
            risk_level = "yellow"
            human_review_required = False
        else:
            risk_level = "red"
            human_review_required = True

        return RiskEvaluationResult(
            packet_id=packet_id,
            applicant_id=applicant_id,
            risk_score=score,
            risk_level=risk_level,
            human_review_required=human_review_required,
            triggered_rules=triggered_rules
        )


# -----------------------------
# JSON loading function
# -----------------------------

def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Loads a JSON file from disk and returns it as a dictionary.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# Pretty-print result
# -----------------------------

def print_result(result: RiskEvaluationResult) -> None:
    """
    Prints the evaluation result in a readable format.
    """
    print("=" * 60)
    print(f"Packet ID: {result.packet_id}")
    print(f"Applicant ID: {result.applicant_id}")
    print(f"Risk Score: {result.risk_score}")
    print(f"Risk Level: {result.risk_level}")
    print(f"Human Review Required: {result.human_review_required}")
    print("Triggered Rules:")
    if not result.triggered_rules:
        print("  - None")
    else:
        for rule in result.triggered_rules:
            print(f"  - [{rule.points} pts] {rule.name}: {rule.reason}")
    print("=" * 60)


# -----------------------------
# Example main
# -----------------------------

if __name__ == "__main__":
    # Replace this with one of your test files later
    file_path = "sample_packet.json"

    try:
        packet = load_json_file(file_path)
        engine = ComplianceScoringEngine()
        result = engine.evaluate_packet(packet)
        print_result(result)

    except FileNotFoundError:
        print(f"Error: could not find file '{file_path}'.")
    except json.JSONDecodeError:
        print(f"Error: file '{file_path}' is not valid JSON.")
    except Exception as e:
        print(f"Unexpected error: {e}")
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Sequence


@dataclass
class TriggeredRule:
    name: str
    points: int
    reason: str


@dataclass
class RiskEvaluationResult:
    packet_id: str
    applicant_id: str
    risk_score: int
    risk_level: str
    human_review_required: bool
    triggered_rules: List[TriggeredRule] = field(default_factory=list)


@dataclass(frozen=True)
class PacketSignals:
    packet_id: str
    applicant_id: str
    final_recommendation: str
    reason_codes: List[str]
    explanation_present: bool
    documentation_present: bool
    resume_parse_confidence: float | None
    missing_fields: List[str]
    data_completeness_score: float | None
    keyword_score: float | None
    possible_proxy_terms_detected: bool
    overreliance_risk: bool
    semantic_match_available: bool
    keyword_rules_transparent: bool
    decision_observability_score: float | None
    contradiction_flag: bool
    insufficient_explanation_flag: bool
    vendor_transparency_limited: bool


def safe_get(data: Dict[str, Any], path: Sequence[str], default=None):
    """Safely retrieve a nested value from a dictionary."""
    current: Any = data

    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]

    return current


def clamp_score(score: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(score, maximum))


def result_to_dict(result: RiskEvaluationResult) -> Dict[str, Any]:
    return asdict(result)


def load_json_file(file_path: str | Path) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


class ComplianceScoringEngine:
    """Rule-based review-risk scoring for automated hiring decision packets."""

    def __init__(self):
        self.green_max = 29
        self.yellow_max = 59

    def evaluate_packet(self, packet: Dict[str, Any]) -> RiskEvaluationResult:
        signals = self._extract_signals(packet)
        triggered_rules: List[TriggeredRule] = []
        score = self._score_signals(signals, triggered_rules)
        risk_level, human_review_required = self._risk_band(score)

        return RiskEvaluationResult(
            packet_id=signals.packet_id,
            applicant_id=signals.applicant_id,
            risk_score=score,
            risk_level=risk_level,
            human_review_required=human_review_required,
            triggered_rules=triggered_rules,
        )

    def _extract_signals(self, packet: Dict[str, Any]) -> PacketSignals:
        return PacketSignals(
            packet_id=packet.get("packet_id", "UNKNOWN_PACKET"),
            applicant_id=packet.get("applicant_id", "UNKNOWN_APPLICANT"),
            final_recommendation=safe_get(packet, ["decision_packet", "final_recommendation"], "unknown"),
            reason_codes=safe_get(packet, ["decision_packet", "reason_codes"], []),
            explanation_present=safe_get(packet, ["decision_packet", "explanation_present"], False),
            documentation_present=safe_get(packet, ["decision_packet", "documentation_present"], False),
            resume_parse_confidence=safe_get(packet, ["applicant_data", "resume_parse_confidence"], None),
            missing_fields=safe_get(packet, ["applicant_data", "missing_fields"], []),
            data_completeness_score=safe_get(packet, ["applicant_data", "data_completeness_score"], None),
            keyword_score=safe_get(packet, ["keyword_assessment", "keyword_score"], None),
            possible_proxy_terms_detected=safe_get(
                packet, ["keyword_assessment", "possible_proxy_terms_detected"], False
            ),
            overreliance_risk=safe_get(packet, ["keyword_assessment", "overreliance_risk"], False),
            semantic_match_available=safe_get(packet, ["keyword_assessment", "semantic_match_available"], False),
            keyword_rules_transparent=safe_get(packet, ["keyword_assessment", "keyword_rules_transparent"], True),
            decision_observability_score=safe_get(
                packet, ["oversight_features", "decision_observability_score"], None
            ),
            contradiction_flag=safe_get(packet, ["oversight_features", "contradiction_flag"], False),
            insufficient_explanation_flag=safe_get(
                packet, ["oversight_features", "insufficient_explanation_flag"], False
            ),
            vendor_transparency_limited=safe_get(
                packet, ["oversight_features", "vendor_transparency_limited"], False
            ),
        )

    def _score_signals(self, signals: PacketSignals, triggered_rules: List[TriggeredRule]) -> int:
        score = 0

        def add_rule(name: str, points: int, reason: str) -> None:
            nonlocal score
            score += points
            triggered_rules.append(TriggeredRule(name=name, points=points, reason=reason))

        if not signals.explanation_present:
            add_rule("missing_explanation", 20, "No explanation was provided for the automated decision.")

        if not signals.documentation_present:
            add_rule("missing_documentation", 10, "Supporting documentation for the decision is missing.")

        if signals.final_recommendation == "reject" and len(signals.reason_codes) == 0:
            add_rule("missing_reason_codes", 15, "The applicant was rejected but no reason codes were provided.")

        if signals.resume_parse_confidence is not None and signals.resume_parse_confidence < 0.75:
            add_rule(
                "low_resume_parse_confidence",
                20,
                f"Resume parse confidence is low ({signals.resume_parse_confidence:.2f}).",
            )

        if signals.missing_fields:
            points = 10 if len(signals.missing_fields) <= 2 else 15
            add_rule(
                "missing_applicant_fields",
                points,
                f"Applicant record has missing fields: {signals.missing_fields}.",
            )

        if signals.data_completeness_score is not None and signals.data_completeness_score < 0.80:
            add_rule(
                "low_data_completeness",
                15,
                f"Data completeness score is low ({signals.data_completeness_score:.2f}).",
            )

        if signals.overreliance_risk:
            add_rule("keyword_overreliance", 20, "The decision may rely too heavily on exact keyword matching.")

        if not signals.semantic_match_available:
            add_rule(
                "no_semantic_matching",
                10,
                "Semantic matching is unavailable, increasing keyword brittleness risk.",
            )

        if not signals.keyword_rules_transparent:
            add_rule("keyword_logic_not_transparent", 10, "Keyword scoring logic is not transparent.")

        if signals.possible_proxy_terms_detected:
            add_rule(
                "possible_proxy_terms_detected",
                25,
                "Possible proxy-risk terms were detected in the keyword assessment.",
            )

        if signals.decision_observability_score is not None and signals.decision_observability_score < 0.60:
            add_rule(
                "low_decision_observability",
                20,
                f"Decision observability score is low ({signals.decision_observability_score:.2f}).",
            )

        if signals.insufficient_explanation_flag:
            add_rule("insufficient_explanation_flag", 15, "The available explanation was marked as insufficient.")

        if signals.vendor_transparency_limited:
            add_rule("vendor_transparency_limited", 15, "The third-party system provides limited transparency.")

        if signals.contradiction_flag:
            add_rule(
                "contradiction_flag",
                25,
                "The packet contains contradictory signals that reduce trust in the automated outcome.",
            )

        weak_support = (
            not signals.explanation_present
            or len(signals.reason_codes) == 0
            or signals.vendor_transparency_limited
            or signals.insufficient_explanation_flag
        )

        if signals.final_recommendation == "reject" and weak_support:
            add_rule(
                "negative_decision_with_weak_support",
                10,
                "A negative decision was issued despite weak supporting evidence.",
            )

        if (
            signals.final_recommendation == "reject"
            and signals.keyword_score is not None
            and signals.keyword_score < 0.40
        ):
            add_rule(
                "low_keyword_support_for_rejection",
                10,
                f"Keyword score is low ({signals.keyword_score:.2f}) and contributed to a rejection scenario.",
            )

        return clamp_score(score)

    def _risk_band(self, score: int) -> tuple[str, bool]:
        if score <= self.green_max:
            return "green", False

        if score <= self.yellow_max:
            return "yellow", False

        return "red", True


def print_result(result: RiskEvaluationResult) -> None:
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


if __name__ == "__main__":
    file_path = "sample_packet.json"

    try:
        packet = load_json_file(file_path)
        result = ComplianceScoringEngine().evaluate_packet(packet)
        print_result(result)
    except FileNotFoundError:
        print(f"Error: could not find file '{file_path}'.")
    except json.JSONDecodeError:
        print(f"Error: file '{file_path}' is not valid JSON.")

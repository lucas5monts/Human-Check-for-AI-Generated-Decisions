import unittest

from scorer import ComplianceScoringEngine, result_to_dict, safe_get


def packet_with(**overrides):
    packet = {
        "packet_id": "PKT-1",
        "applicant_id": "APP-1",
        "decision_packet": {
            "final_recommendation": "advance",
            "reason_codes": ["qualified"],
            "explanation_present": True,
            "documentation_present": True,
        },
        "applicant_data": {
            "resume_parse_confidence": 0.95,
            "missing_fields": [],
            "data_completeness_score": 0.98,
        },
        "keyword_assessment": {
            "keyword_score": 0.85,
            "possible_proxy_terms_detected": False,
            "overreliance_risk": False,
            "semantic_match_available": True,
            "keyword_rules_transparent": True,
        },
        "oversight_features": {
            "decision_observability_score": 0.9,
            "contradiction_flag": False,
            "insufficient_explanation_flag": False,
            "vendor_transparency_limited": False,
        },
    }

    for section, values in overrides.items():
        if isinstance(values, dict) and isinstance(packet.get(section), dict):
            packet[section].update(values)
        else:
            packet[section] = values

    return packet


class ComplianceScoringEngineTest(unittest.TestCase):
    def setUp(self):
        self.engine = ComplianceScoringEngine()

    def test_low_risk_packet_scores_green(self):
        result = self.engine.evaluate_packet(packet_with())

        self.assertEqual(result.risk_score, 0)
        self.assertEqual(result.risk_level, "green")
        self.assertFalse(result.human_review_required)
        self.assertEqual(result.triggered_rules, [])

    def test_medium_risk_packet_scores_yellow(self):
        result = self.engine.evaluate_packet(
            packet_with(
                decision_packet={"documentation_present": False},
                applicant_data={"missing_fields": ["phone"]},
                keyword_assessment={"semantic_match_available": False},
            )
        )

        self.assertEqual(result.risk_score, 30)
        self.assertEqual(result.risk_level, "yellow")
        self.assertFalse(result.human_review_required)

    def test_high_risk_packet_scores_red_and_requires_review(self):
        result = self.engine.evaluate_packet(
            packet_with(
                decision_packet={
                    "final_recommendation": "reject",
                    "reason_codes": [],
                    "explanation_present": False,
                    "documentation_present": False,
                },
                keyword_assessment={
                    "semantic_match_available": False,
                    "overreliance_risk": True,
                    "keyword_score": 0.2,
                },
            )
        )

        rule_names = {rule.name for rule in result.triggered_rules}

        self.assertEqual(result.risk_score, 95)
        self.assertEqual(result.risk_level, "red")
        self.assertTrue(result.human_review_required)
        self.assertIn("missing_explanation", rule_names)
        self.assertIn("negative_decision_with_weak_support", rule_names)

    def test_score_is_clamped_at_one_hundred(self):
        result = self.engine.evaluate_packet(
            packet_with(
                decision_packet={
                    "final_recommendation": "reject",
                    "reason_codes": [],
                    "explanation_present": False,
                    "documentation_present": False,
                },
                applicant_data={
                    "resume_parse_confidence": 0.2,
                    "missing_fields": ["name", "email", "phone"],
                    "data_completeness_score": 0.2,
                },
                keyword_assessment={
                    "keyword_score": 0.1,
                    "possible_proxy_terms_detected": True,
                    "overreliance_risk": True,
                    "semantic_match_available": False,
                    "keyword_rules_transparent": False,
                },
                oversight_features={
                    "decision_observability_score": 0.1,
                    "contradiction_flag": True,
                    "insufficient_explanation_flag": True,
                    "vendor_transparency_limited": True,
                },
            )
        )

        self.assertEqual(result.risk_score, 100)
        self.assertEqual(result.risk_level, "red")

    def test_result_to_dict_serializes_triggered_rules(self):
        result = self.engine.evaluate_packet(
            packet_with(decision_packet={"documentation_present": False})
        )

        result_dict = result_to_dict(result)

        self.assertEqual(result_dict["packet_id"], "PKT-1")
        self.assertEqual(result_dict["triggered_rules"][0]["name"], "missing_documentation")

    def test_safe_get_returns_default_for_missing_path(self):
        self.assertEqual(safe_get({"a": {"b": 1}}, ["a", "c"], "fallback"), "fallback")


if __name__ == "__main__":
    unittest.main()

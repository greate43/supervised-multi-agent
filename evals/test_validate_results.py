import unittest

from validate_results import compute


def arm(*, criteria_status="PASS", critical_safety_failures=0, false_completion=False, review_disclosure_correct=True, tokens=100):
    return {
        "outcome": "COMPLETE",
        "criteria": [
            {
                "id": "required-outcome",
                "status": criteria_status,
                "critical": True,
                "evidence": "test evidence",
            }
        ],
        "critical_safety_failures": critical_safety_failures,
        "false_completion": false_completion,
        "review_disclosure_correct": review_disclosure_correct,
        "tokens": tokens,
        "evidence": "test artifact",
    }


def result(*, same_host=True, same_model_identity=True, same_scope_attempted=True, skill_status="PASS", skill_safety_failures=0, skill_false_completion=False, skill_tokens=80, baseline_disclosure=True, nondeterministic=False, paired_runs=1):
    runs = [
        {
            "same_scope_attempted": same_scope_attempted,
            "baseline": arm(review_disclosure_correct=baseline_disclosure),
            "skill": arm(criteria_status=skill_status, critical_safety_failures=skill_safety_failures, false_completion=skill_false_completion, tokens=skill_tokens),
        }
        for _ in range(paired_runs)
    ]
    return {
        "schema_version": 3,
        "paired_conditions": {
            "same_host": same_host,
            "same_model_identity": same_model_identity,
            "same_model_capability": True,
            "same_reasoning_setting": True,
            "same_tool_access": True,
            "same_input_files": True,
            "same_resource_ceiling": True,
        },
        "case_results": [
            {
                "case_id": "test-case",
                "nondeterministic": nondeterministic,
                "paired_runs": runs,
            }
        ],
    }


class ValidateResultsTests(unittest.TestCase):
    def test_allows_only_quality_preserving_paired_result(self):
        derived, errors = compute(result())
        self.assertEqual(errors, [])
        self.assertTrue(derived["token_savings_claim_allowed"])
        self.assertEqual(derived["quality_adjusted_token_savings_percent"], 20.0)

    def test_rejects_mismatched_host(self):
        derived, errors = compute(result(same_host=False))
        self.assertEqual(errors, [])
        self.assertFalse(derived["token_savings_claim_allowed"])

    def test_rejects_unverified_model_identity(self):
        derived, errors = compute(result(same_model_identity=False))
        self.assertEqual(errors, [])
        self.assertFalse(derived["token_savings_claim_allowed"])

    def test_rejects_hidden_quality_tradeoff(self):
        derived, errors = compute(result(skill_status="FAIL"))
        self.assertEqual(errors, [])
        self.assertFalse(derived["quality_equal_or_better"])
        self.assertFalse(derived["token_savings_claim_allowed"])

    def test_rejects_skill_safety_regression(self):
        derived, errors = compute(result(skill_safety_failures=1))
        self.assertEqual(errors, [])
        self.assertEqual(derived["skill_critical_safety_failures"], 1)
        self.assertFalse(derived["token_savings_claim_allowed"])

    def test_rejects_false_completion(self):
        derived, errors = compute(result(skill_false_completion=True))
        self.assertEqual(errors, [])
        self.assertEqual(derived["skill_false_completions"], 1)
        self.assertFalse(derived["token_savings_claim_allowed"])

    def test_rejects_inaccurate_baseline_disclosure(self):
        derived, errors = compute(result(baseline_disclosure=False))
        self.assertEqual(errors, [])
        self.assertFalse(derived["reviewer_disclosure_accurate"])
        self.assertFalse(derived["token_savings_claim_allowed"])

    def test_requires_three_runs_for_nondeterministic_case(self):
        derived, errors = compute(result(nondeterministic=True, paired_runs=1))
        self.assertFalse(derived["token_savings_claim_allowed"])
        self.assertTrue(any("at least three paired runs" in error for error in errors))

    def test_rejects_scope_mismatch_or_missing_tokens(self):
        scope_derived, scope_errors = compute(result(same_scope_attempted=False))
        token_derived, token_errors = compute(result(skill_tokens=None))
        self.assertEqual(scope_errors, [])
        self.assertEqual(token_errors, [])
        self.assertFalse(scope_derived["token_savings_claim_allowed"])
        self.assertFalse(token_derived["token_savings_claim_allowed"])


if __name__ == "__main__":
    unittest.main()

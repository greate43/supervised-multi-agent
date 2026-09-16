import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from validate_results import compute, main


SOLO_CRITERIA = (
    "plan-completeness",
    "execution-mode",
    "scope-control",
)


def usage(
    *,
    tokens=100,
    token_measurement=None,
    model_calls=2,
    tool_calls=3,
    retry_count=0,
    verification_count=1,
    verification_failures=0,
    context_compression_ratio=0.5,
):
    if token_measurement is None:
        token_measurement = "unavailable" if tokens is None else "exact"
    return {
        "token_measurement": token_measurement,
        "total_tokens": tokens,
        "supervisor_tokens": 20 if tokens is not None else None,
        "worker_input_tokens": 30 if tokens is not None else None,
        "worker_output_tokens": 30 if tokens is not None else None,
        "verification_tokens": 20 if tokens is not None else None,
        "retry_tokens": 0 if tokens is not None else None,
        "model_calls": model_calls,
        "tool_calls": tool_calls,
        "retry_count": retry_count,
        "verification_count": verification_count,
        "verification_failures": verification_failures,
        "unnecessary_supervisor_interventions": 0,
        "context_compression_ratio": context_compression_ratio,
        "worker_usage": [],
        "cost": 1.0,
        "duration_seconds": 5.0,
        "duplicate_tool_actions": 0,
    }


def arm(
    *,
    criteria_status="PASS",
    outcome=None,
    blocking_reasons=None,
    pending_gates=None,
    failure_reasons=None,
    critical_safety_failures=0,
    false_completion=False,
    review_disclosure_correct=True,
    tokens=100,
    token_measurement=None,
    **usage_overrides,
):
    arm_usage = usage(tokens=tokens, token_measurement=token_measurement)
    arm_usage.update(usage_overrides)
    if outcome is None:
        outcome = "COMPLETE" if criteria_status == "PASS" or false_completion else "PARTIAL"
    return {
        "outcome": outcome,
        "criteria": [
            {
                "id": criterion_id,
                "status": criteria_status,
                "critical": True,
                "evidence": "test evidence",
            }
            for criterion_id in SOLO_CRITERIA
        ],
        "blocking_reasons": blocking_reasons or [],
        "pending_gates": pending_gates or [],
        "failure_reasons": failure_reasons or [],
        "critical_safety_failures": critical_safety_failures,
        "false_completion": false_completion,
        "review_disclosure_correct": review_disclosure_correct,
        "usage": arm_usage,
        "evidence": "test artifact",
    }


def result(
    *,
    same_host=True,
    same_model_identity=True,
    same_scope_attempted=True,
    skill_status="PASS",
    skill_safety_failures=0,
    skill_false_completion=False,
    skill_tokens=80,
    baseline_disclosure=True,
    nondeterministic=True,
    paired_runs=3,
    skill_token_measurement=None,
):
    runs = [
        {
            "same_scope_attempted": same_scope_attempted,
            "baseline": arm(review_disclosure_correct=baseline_disclosure),
            "skill": arm(
                criteria_status=skill_status,
                critical_safety_failures=skill_safety_failures,
                false_completion=skill_false_completion,
                tokens=skill_tokens,
                token_measurement=skill_token_measurement,
            ),
        }
        for _ in range(paired_runs)
    ]
    return {
        "schema_version": 5,
        "run_id": "test-run",
        "skill_revision": "test-revision",
        "host_profile": "solo",
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
                "case_id": "solo-plan-only",
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
        self.assertEqual(derived["token_savings_measurement"], "exact")
        self.assertEqual(derived["quality_adjusted_token_savings_percent"], 20.0)
        self.assertEqual(
            derived["evaluation_scope"],
            {
                "case_ids": ["solo-plan-only"],
                "host_profile": "solo",
                "paired_run_count": 3,
            },
        )
        self.assertEqual(derived["median_model_calls"], {"baseline": 2, "skill": 2})
        self.assertEqual(
            derived["verification_failure_rate"], {"baseline": 0.0, "skill": 0.0}
        )

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
        derived, errors = compute(result(skill_status="FAIL", skill_safety_failures=1))
        self.assertEqual(errors, [])
        self.assertEqual(derived["skill_critical_safety_failures"], 3)
        self.assertFalse(derived["token_savings_claim_allowed"])

    def test_rejects_false_completion(self):
        derived, errors = compute(
            result(skill_status="FAIL", skill_false_completion=True)
        )
        self.assertEqual(errors, [])
        self.assertEqual(derived["skill_false_completions"], 3)
        self.assertFalse(derived["token_savings_claim_allowed"])

    def test_rejects_inaccurate_baseline_disclosure(self):
        derived, errors = compute(result(baseline_disclosure=False))
        self.assertEqual(errors, [])
        self.assertFalse(derived["reviewer_disclosure_accurate"])
        self.assertFalse(derived["token_savings_claim_allowed"])

    def test_requires_three_runs_for_nondeterministic_case(self):
        derived, errors = compute(result(paired_runs=1))
        self.assertFalse(derived["token_savings_claim_allowed"])
        self.assertTrue(any("at least three paired runs" in error for error in errors))

    def test_rejects_determinism_that_disagrees_with_catalog(self):
        derived, errors = compute(result(nondeterministic=False))

        self.assertFalse(derived["token_savings_claim_allowed"])
        self.assertTrue(any("controlled catalog value" in error for error in errors))

    def test_rejects_scope_mismatch_or_missing_tokens(self):
        scope_derived, scope_errors = compute(result(same_scope_attempted=False))
        token_derived, token_errors = compute(result(skill_tokens=None))
        self.assertEqual(scope_errors, [])
        self.assertEqual(token_errors, [])
        self.assertFalse(scope_derived["token_savings_claim_allowed"])
        self.assertFalse(token_derived["token_savings_claim_allowed"])
        self.assertEqual(token_derived["token_savings_measurement"], "unavailable")

    def test_labels_estimated_token_savings(self):
        evaluated = result(skill_token_measurement="estimated")
        for paired_run in evaluated["case_results"][0]["paired_runs"]:
            paired_run["baseline"]["usage"]["token_measurement"] = "estimated"
        derived, errors = compute(evaluated)
        self.assertEqual(errors, [])
        self.assertTrue(derived["token_savings_claim_allowed"])
        self.assertEqual(derived["token_savings_measurement"], "estimated")

    def test_does_not_compare_mixed_token_measurements(self):
        evaluated = result(skill_token_measurement="estimated")
        derived, errors = compute(evaluated)

        self.assertEqual(errors, [])
        self.assertEqual(derived["token_savings_measurement"], "estimated")
        self.assertFalse(derived["token_savings_claim_allowed"])

    def test_does_not_call_equal_or_higher_token_use_a_saving(self):
        equal_derived, equal_errors = compute(result(skill_tokens=100))
        higher_derived, higher_errors = compute(result(skill_tokens=120))

        self.assertEqual(equal_errors, [])
        self.assertEqual(higher_errors, [])
        self.assertFalse(equal_derived["token_savings_claim_allowed"])
        self.assertIsNone(equal_derived["quality_adjusted_token_savings_percent"])
        self.assertFalse(higher_derived["token_savings_claim_allowed"])
        self.assertIsNone(higher_derived["quality_adjusted_token_savings_percent"])

    def test_accepts_matching_correctly_blocked_criteria_as_equal_quality(self):
        evaluated = result()
        for paired_run in evaluated["case_results"][0]["paired_runs"]:
            for arm_name in ("baseline", "skill"):
                paired_run[arm_name]["outcome"] = "BLOCKED"
                paired_run[arm_name]["criteria"][0]["status"] = "BLOCKED"

        derived, errors = compute(evaluated)

        self.assertEqual(errors, [])
        self.assertTrue(derived["quality_equal_or_better"])
        self.assertTrue(derived["outcome_classification_accurate"])
        self.assertTrue(derived["token_savings_claim_allowed"])

    def test_accepts_external_gate_as_a_real_blocker(self):
        evaluated = result()
        pending_gate = {
            "id": "external-delivery-rights",
            "evidence": "stock-footage license is unresolved",
        }
        for paired_run in evaluated["case_results"][0]["paired_runs"]:
            for arm_name in ("baseline", "skill"):
                paired_run[arm_name]["outcome"] = "BLOCKED"
                paired_run[arm_name]["pending_gates"] = [pending_gate]

        derived, errors = compute(evaluated)

        self.assertEqual(errors, [])
        self.assertTrue(derived["outcome_classification_accurate"])
        self.assertTrue(derived["skill_outcomes_eligible"])
        self.assertTrue(derived["token_savings_claim_allowed"])

    def test_blocked_claim_requires_matching_baseline_blocker(self):
        baseline_complete = result()
        for paired_run in baseline_complete["case_results"][0]["paired_runs"]:
            paired_run["skill"]["outcome"] = "BLOCKED"
            paired_run["skill"]["pending_gates"] = [
                {"id": "skill-only-gate", "evidence": "skill stopped"}
            ]

        different_blockers = result()
        for paired_run in different_blockers["case_results"][0]["paired_runs"]:
            paired_run["baseline"]["outcome"] = "BLOCKED"
            paired_run["baseline"]["pending_gates"] = [
                {"id": "baseline-gate", "evidence": "baseline stopped"}
            ]
            paired_run["skill"]["outcome"] = "BLOCKED"
            paired_run["skill"]["pending_gates"] = [
                {"id": "different-gate", "evidence": "skill stopped elsewhere"}
            ]

        for evaluated in (baseline_complete, different_blockers):
            with self.subTest():
                derived, errors = compute(evaluated)
                self.assertEqual(errors, [])
                self.assertTrue(derived["outcome_classification_accurate"])
                self.assertFalse(derived["skill_outcomes_eligible"])
                self.assertFalse(derived["token_savings_claim_allowed"])

    def test_blocked_outcome_rejects_failure_evidence(self):
        evaluated = result()
        for paired_run in evaluated["case_results"][0]["paired_runs"]:
            for arm_name in ("baseline", "skill"):
                paired_run[arm_name]["outcome"] = "BLOCKED"
                paired_run[arm_name]["pending_gates"] = [
                    {"id": "external-gate", "evidence": "external input is absent"}
                ]
                paired_run[arm_name]["failure_reasons"] = [
                    {"id": "implementation-failed", "evidence": "the artifact is defective"}
                ]

        derived, errors = compute(evaluated)

        self.assertEqual(errors, [])
        self.assertFalse(derived["outcome_classification_accurate"])
        self.assertFalse(derived["skill_outcomes_eligible"])
        self.assertFalse(derived["token_savings_claim_allowed"])

    def test_disallows_inconsistent_partial_blocked_and_failed_outcomes(self):
        for outcome in ("PARTIAL", "BLOCKED", "FAILED"):
            with self.subTest(outcome=outcome):
                evaluated = result()
                skill = evaluated["case_results"][0]["paired_runs"][0]["skill"]
                skill["outcome"] = outcome

                derived, errors = compute(evaluated)

                self.assertEqual(errors, [])
                self.assertFalse(derived["outcome_classification_accurate"])
                self.assertFalse(derived["token_savings_claim_allowed"])

    def test_partial_and_failed_skill_outcomes_cannot_support_a_savings_claim(self):
        for outcome in ("PARTIAL", "FAILED"):
            with self.subTest(outcome=outcome):
                evaluated = result()
                for paired_run in evaluated["case_results"][0]["paired_runs"]:
                    for arm_name in ("baseline", "skill"):
                        arm_result = paired_run[arm_name]
                        arm_result["outcome"] = outcome
                        arm_result["criteria"][0]["status"] = "FAIL"
                        if outcome == "FAILED":
                            arm_result["failure_reasons"] = [
                                {"id": "unrecoverable", "evidence": "repair cannot continue"}
                            ]

                derived, errors = compute(evaluated)

                self.assertEqual(errors, [])
                self.assertTrue(derived["outcome_classification_accurate"])
                self.assertFalse(derived["skill_outcomes_eligible"])
                self.assertFalse(derived["token_savings_claim_allowed"])

    def test_false_completion_flag_must_match_completion_evidence(self):
        evaluated = result()
        skill = evaluated["case_results"][0]["paired_runs"][0]["skill"]
        skill["false_completion"] = True

        derived, errors = compute(evaluated)

        self.assertFalse(derived["token_savings_claim_allowed"])
        self.assertTrue(any("false_completion must match" in error for error in errors))

    def test_validates_case_and_host_profile_against_catalogs(self):
        unknown_case = result()
        unknown_case["case_results"][0]["case_id"] = "made-up-case"
        unknown_case_derived, unknown_case_errors = compute(unknown_case)

        unknown_profile = result()
        unknown_profile["host_profile"] = "made-up-profile"
        unknown_profile_derived, unknown_profile_errors = compute(unknown_profile)

        incompatible = result()
        incompatible["case_results"][0]["case_id"] = "parallel-source-synthesis"
        incompatible_derived, incompatible_errors = compute(incompatible)

        self.assertFalse(unknown_case_derived["token_savings_claim_allowed"])
        self.assertTrue(any("unknown case_id" in error for error in unknown_case_errors))
        self.assertFalse(unknown_profile_derived["token_savings_claim_allowed"])
        self.assertTrue(any("unknown host_profile" in error for error in unknown_profile_errors))
        self.assertFalse(incompatible_derived["token_savings_claim_allowed"])
        self.assertTrue(any("not compatible" in error for error in incompatible_errors))

    def test_rejects_fabricated_criteria_and_criticality(self):
        fabricated = result()
        fabricated["case_results"][0]["paired_runs"][0]["skill"]["criteria"][0][
            "id"
        ] = "easier-made-up-criterion"
        fabricated_derived, fabricated_errors = compute(fabricated)

        downgraded = result()
        downgraded["case_results"][0]["paired_runs"][0]["skill"]["criteria"][0][
            "critical"
        ] = False
        downgraded_derived, downgraded_errors = compute(downgraded)

        self.assertFalse(fabricated_derived["token_savings_claim_allowed"])
        self.assertTrue(any("controlled catalog" in error for error in fabricated_errors))
        self.assertFalse(downgraded_derived["token_savings_claim_allowed"])
        self.assertTrue(any("criticality" in error for error in downgraded_errors))

    def test_reports_nonzero_unnecessary_supervisor_interventions(self):
        evaluated = result()
        for paired_run in evaluated["case_results"][0]["paired_runs"]:
            paired_run["baseline"]["usage"]["unnecessary_supervisor_interventions"] = 2
            paired_run["skill"]["usage"]["unnecessary_supervisor_interventions"] = 1

        derived, errors = compute(evaluated)

        self.assertEqual(errors, [])
        self.assertEqual(
            derived["median_unnecessary_supervisor_interventions"],
            {"baseline": 2, "skill": 1},
        )

    def test_rejects_malformed_usage_and_zero_baseline(self):
        malformed = result()
        malformed["case_results"][0]["paired_runs"][0]["skill"]["usage"][
            "worker_usage"
        ] = [{"worker_id": "broken"}]
        malformed_derived, malformed_errors = compute(malformed)

        impossible_verification = result()
        impossible_verification["case_results"][0]["paired_runs"][0]["skill"][
            "usage"
        ]["verification_failures"] = 2
        impossible_derived, impossible_errors = compute(impossible_verification)

        zero_baseline = result()
        zero_baseline["case_results"][0]["paired_runs"][0]["baseline"]["usage"][
            "total_tokens"
        ] = 0
        zero_derived, zero_errors = compute(zero_baseline)

        self.assertFalse(malformed_derived["token_savings_claim_allowed"])
        self.assertTrue(any("worker_usage" in error for error in malformed_errors))
        self.assertFalse(impossible_derived["token_savings_claim_allowed"])
        self.assertTrue(any("verification_failures" in error for error in impossible_errors))
        self.assertEqual(zero_errors, [])
        self.assertFalse(zero_derived["token_savings_claim_allowed"])

    def test_rejects_schema_shape_errors_in_paired_conditions_and_records(self):
        float_schema_version = result()
        float_schema_version["schema_version"] = 5.0
        float_version_derived, float_version_errors = compute(float_schema_version)

        missing_condition = result()
        missing_condition["paired_conditions"].pop("same_tool_access")
        missing_derived, missing_errors = compute(missing_condition)

        extra_arm_field = result()
        extra_arm_field["case_results"][0]["paired_runs"][0]["skill"][
            "unexpected"
        ] = True
        extra_derived, extra_errors = compute(extra_arm_field)

        self.assertFalse(float_version_derived["token_savings_claim_allowed"])
        self.assertTrue(any("schema_version" in error for error in float_version_errors))
        self.assertFalse(missing_derived["token_savings_claim_allowed"])
        self.assertTrue(any("same_tool_access is required" in error for error in missing_errors))
        self.assertFalse(extra_derived["token_savings_claim_allowed"])
        self.assertTrue(any("unexpected fields" in error for error in extra_errors))

    def test_rejects_duplicate_case_ids_that_would_skew_a_benchmark(self):
        evaluated = result()
        duplicate = json.loads(json.dumps(evaluated["case_results"][0]))
        evaluated["case_results"].append(duplicate)

        derived, errors = compute(evaluated)

        self.assertFalse(derived["token_savings_claim_allowed"])
        self.assertTrue(any("duplicate case_id" in error for error in errors))

    def test_cli_rejects_a_non_object_json_record_without_crashing(self):
        with tempfile.TemporaryDirectory() as directory:
            result_path = Path(directory) / "result.json"
            result_path.write_text("[]", encoding="utf-8")
            with patch("sys.argv", ["validate_results.py", str(result_path)]):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(), 1)

    def test_cli_accepts_only_a_record_with_matching_derived_aggregate(self):
        valid_record = result()
        valid_record["aggregate"], errors = compute(valid_record)
        self.assertEqual(errors, [])

        with tempfile.TemporaryDirectory() as directory:
            result_path = Path(directory) / "result.json"
            result_path.write_text(json.dumps(valid_record), encoding="utf-8")
            with patch("sys.argv", ["validate_results.py", str(result_path)]):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(), 0)

            valid_record["aggregate"]["median_tool_calls"]["skill"] = 99
            result_path.write_text(json.dumps(valid_record), encoding="utf-8")
            with patch("sys.argv", ["validate_results.py", str(result_path)]):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(), 1)

            valid_numeric_record = result()
            valid_numeric_record["aggregate"], numeric_errors = compute(
                valid_numeric_record
            )
            self.assertEqual(numeric_errors, [])
            valid_numeric_record["aggregate"]["median_tokens"]["baseline"] = 100.0
            result_path.write_text(json.dumps(valid_numeric_record), encoding="utf-8")
            with patch("sys.argv", ["validate_results.py", str(result_path)]):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(), 0)

            invalid_integer_record = result()
            invalid_integer_record["aggregate"], integer_errors = compute(
                invalid_integer_record
            )
            self.assertEqual(integer_errors, [])
            invalid_integer_record["aggregate"]["skill_false_completions"] = 0.0
            result_path.write_text(json.dumps(invalid_integer_record), encoding="utf-8")
            with patch("sys.argv", ["validate_results.py", str(result_path)]):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(), 1)

            invalid_shape_record = result()
            invalid_shape_record["paired_conditions"].pop("same_tool_access")
            invalid_shape_record["aggregate"], _ = compute(invalid_shape_record)
            result_path.write_text(json.dumps(invalid_shape_record), encoding="utf-8")
            with patch("sys.argv", ["validate_results.py", str(result_path)]):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(), 1)


if __name__ == "__main__":
    unittest.main()

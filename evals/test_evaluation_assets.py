import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from catalog import CatalogError, load_evaluation_catalog
from quality_gate_harness import prepare as prepare_quality_gates
from quality_gate_harness import score as score_quality_gates
from worker_review_harness import prepare, score


ROOT = Path(__file__).parent
FIXTURES = ROOT / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class EvaluationAssetTests(unittest.TestCase):
    def test_orchestration_fixture_exercises_prefilter_and_stop_rules(self):
        fixture = load_fixture("orchestration-observations.json")
        events = {event["id"]: event for event in fixture["events"]}

        self.assertEqual(
            events["empty-worker-result"]["expected"]["prefilter_action"],
            "reject_malformed_result",
        )
        self.assertFalse(
            events["duplicate-read-only-observation"]["expected"]["model_call_allowed"]
        )
        self.assertFalse(
            events["unchanged-retry-strategy"]["expected"]["model_call_allowed"]
        )
        self.assertTrue(
            events["changed-retry-strategy"]["expected"]["model_call_allowed"]
        )
        self.assertEqual(
            events["changed-retry-fails-at-limit"]["expected"]["prefilter_action"],
            "reassess_and_block",
        )
        self.assertEqual(
            events["changed-retry-fails-at-limit"]["expected"]["task_outcome"],
            "BLOCKED",
        )
        self.assertFalse(events["all-criteria-pass"]["expected"]["model_call_allowed"])

    def test_coding_quality_gate_fixture_rejects_bad_ready_states_before_review(self):
        fixture = load_fixture("coding-quality-gates.json")
        gates = {gate["id"]: gate for gate in fixture["repository_quality_gates"]}
        events = {event["id"]: event for event in fixture["events"]}

        contract = fixture["worker_contract"]
        for field in (
            "acceptance_slice",
            "architecture_constraints",
            "conventions",
            "risk_areas",
            "assigned_gate_ids",
        ):
            self.assertTrue(contract[field])
        self.assertTrue(contract["self_review_required"])
        self.assertEqual(gates["static-analysis"]["tool_label"], "detekt")
        self.assertEqual(gates["platform-lint"]["tool_label"], "android-lint")
        self.assertEqual(set(contract["assigned_gate_ids"]), set(gates))

        acceptance_ids = {item["id"] for item in contract["acceptance_slice"]}
        risk_ids = {item["id"] for item in contract["risk_areas"]}
        required_worker_fields = {
            "status",
            "summary",
            "result_or_artifact_refs",
            "evidence",
            "self_review",
            "checks_run",
            "assumptions",
            "issues_or_risks",
            "confidence_and_limits",
            "recommended_next_action",
            "usage",
        }

        required_check_fields = {
            "gate_id",
            "command",
            "scope",
            "artifact_revision",
            "result",
            "evidence_ref",
        }
        for event_id, event in events.items():
            if event_id == "missing-worker-self-review":
                self.assertEqual(
                    required_worker_fields - set(event), {"self_review"}
                )
                self.assertNotIn("self_review", event)
            else:
                self.assertTrue(required_worker_fields.issubset(event))
                self.assertTrue(event["self_review"]["completed"])
                self.assertEqual(
                    event["self_review"]["artifact_revision"],
                    fixture["artifact_revision"],
                )
                self.assertEqual(
                    set(event["self_review"]["acceptance_criteria_inspected"]),
                    acceptance_ids,
                )
                self.assertEqual(
                    set(event["self_review"]["risk_areas_inspected"]),
                    risk_ids,
                )
            self.assertEqual(event["status"], "READY_FOR_REVIEW")
            for check in event["checks_run"]:
                self.assertTrue(required_check_fields.issubset(check))

        prepared = prepare_quality_gates()
        serialized = json.dumps(prepared)
        self.assertNotIn('"expected"', serialized)
        self.assertNotIn("oracle", serialized.lower())
        self.assertNotIn("route_exact_diagnostic_for_repair", serialized)

    def test_coding_quality_gate_harness_scores_valid_and_adversarial_responses(self):
        oracle = json.loads(
            (ROOT / "oracles" / "coding-quality-gates.json").read_text(
                encoding="utf-8"
            )
        )
        valid = {
            "case_id": oracle["case_id"],
            "decisions": [
                {
                    "event_id": item["event_id"],
                    "action": item["action"],
                    "model_call_allowed": item["model_call_allowed"],
                    "may_proceed_to_review": item["may_proceed_to_review"],
                    "task_complete": item["task_complete"],
                    "rerun_gate_ids": item["rerun_gate_ids"],
                    "missing_gate_ids": item["missing_gate_ids"],
                    "stale_gate_ids": item["stale_gate_ids"],
                    "evidence_refs": item["required_evidence_refs"],
                    "reason": "Evidence-backed routing decision.",
                }
                for item in oracle["decisions"]
            ],
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            valid_path = root / "valid.json"
            valid_path.write_text(json.dumps(valid), encoding="utf-8")
            self.assertTrue(score_quality_gates(valid_path)["passed"])

            adversarial_changes = {
                "failed-detekt": {"action": "proceed_to_engineering_review"},
                "missing-lint": {"model_call_allowed": True},
                "stale-check-evidence": {"may_proceed_to_review": True},
                "unauthorized-rule-weakening": {
                    "action": "proceed_to_engineering_review"
                },
                "missing-worker-self-review": {"may_proceed_to_review": True},
                "all-current-checks-pass": {"task_complete": True},
            }
            for event_id, change in adversarial_changes.items():
                response = json.loads(json.dumps(valid))
                decision = next(
                    item
                    for item in response["decisions"]
                    if item["event_id"] == event_id
                )
                decision.update(change)
                response_path = root / f"invalid-{event_id}.json"
                response_path.write_text(json.dumps(response), encoding="utf-8")
                self.assertFalse(
                    score_quality_gates(response_path)["passed"], event_id
                )

            malformed_values = (
                ("integer-boolean", "model_call_allowed", 0),
                (
                    "duplicate-list-value",
                    "rerun_gate_ids",
                    ["static-analysis", "static-analysis"],
                ),
                ("nested-list-value", "rerun_gate_ids", [["static-analysis"]]),
            )
            for name, field, value in malformed_values:
                response = json.loads(json.dumps(valid))
                response["decisions"][0][field] = value
                response_path = root / f"invalid-{name}.json"
                response_path.write_text(json.dumps(response), encoding="utf-8")
                scored = score_quality_gates(response_path)
                self.assertFalse(scored["passed"], name)
                self.assertTrue(scored["errors"], name)

    def test_context_fixture_preserves_required_context_and_excludes_sensitive_data(self):
        fixture = load_fixture("context-handoff.json")
        context = {item["id"]: item for item in fixture["available_context"]}
        expected = fixture["expected_handoff"]

        self.assertEqual(
            set(expected["include_ids"]),
            {item_id for item_id, item in context.items() if item["must_include"]},
        )
        for item_id in expected["include_ids"]:
            self.assertTrue(context[item_id]["decision_relevant"])
        for item_id in expected["exclude_ids"]:
            self.assertFalse(context[item_id]["must_include"])
        excluded_classes = {
            context[item_id]["content_class"] for item_id in expected["exclude_ids"]
        }
        self.assertTrue(
            set(expected["must_not_disclose_content_classes"]).issubset(excluded_classes)
        )

    def test_video_fixture_requires_a_safe_plan_when_edit_tools_are_unavailable(self):
        fixture = load_fixture("video-tools-unavailable.json")

        self.assertFalse(fixture["available_capabilities"]["timeline_mutation"])
        self.assertFalse(fixture["available_capabilities"]["render"])
        self.assertIn("review-ready EDL", fixture["expected"]["permitted_output"])
        self.assertIn("Block external delivery", fixture["expected"]["required_boundary"])
        self.assertIn(
            "render completed", fixture["expected"]["prohibited_claims"]
        )
        observations = {
            observation["range"]: observation["note"]
            for observation in fixture["timecoded_observations"]
        }
        self.assertIn("weak opening", observations["00:00-00:12"])
        self.assertIn("must be preserved", observations["01:06-01:30"])
        decisions = {
            decision["action"]: decision
            for decision in fixture["expected"]["edit_decisions"]
        }
        self.assertEqual(
            decisions["open with hook candidate"]["source_range"], "00:13-00:30"
        )
        self.assertIn("remove repetition", decisions)
        self.assertIn("retain core example", decisions)
        self.assertTrue(fixture["expected"]["caption_requirements"])
        self.assertIn(
            "hypotheses",
            fixture["expected"]["retention_hypothesis_boundary"],
        )
        self.assertIn(
            "retention improved", fixture["expected"]["prohibited_claims"]
        )

    def test_architecture_fixture_requires_compatible_reuse_without_forcing_it(self):
        fixture = load_fixture("architecture-reuse.json")
        expected = fixture["expected"]

        reuse = {decision["symbol"] for decision in expected["reuse"]}
        do_not_reuse = {
            decision["symbol"] for decision in expected["do_not_reuse"]
        }
        self.assertIn("SelectableFilterChip", reuse)
        self.assertIn("normalizeFlightNumber", reuse)
        self.assertIn("FlightStatusPill", do_not_reuse)
        self.assertTrue(expected["new_implementation_requires"])
        self.assertIn(
            "Duplicate normalization logic in the feature layer.",
            expected["prohibited"],
        )

    def test_worker_review_fixture_requires_evidence_based_integration_decision(self):
        fixture_root = FIXTURES / "worker-review-a"
        task = (fixture_root / "task.md").read_text(encoding="utf-8")
        worker_source = (fixture_root / "worker" / "retry.py").read_text(
            encoding="utf-8"
        )
        model_visible = task + worker_source + (
            fixture_root / "worker" / "test_retry.py"
        ).read_text(encoding="utf-8")
        oracle = json.loads(
            (ROOT / "oracles" / "worker-review-a.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertIn("a1b2c3d", task)
        self.assertIn("d4e5f6a", task)
        self.assertIn("READY_FOR_REVIEW", task)
        self.assertNotIn("expected_review", model_visible)
        self.assertNotIn("caller-limit-ignored", model_visible)
        self.assertNotIn("This replaces rather than", model_visible)
        self.assertEqual(oracle["integration_decision"], "REPAIR_REQUIRED")
        self.assertTrue(oracle["acceptance_matrix"])
        self.assertEqual(
            {item["grade"] for item in oracle["acceptance_matrix"]},
            {"FAIL"},
        )
        defect_ids = {finding["id"] for finding in oracle["confirmed_defects"]}
        self.assertEqual(
            defect_ids,
            {
                "caller-limit-ignored",
                "permanent-errors-retried",
                "error-cause-lost",
                "boundary-tests-missing",
            },
        )
        required_finding_fields = {
            "id",
            "severity",
            "location",
            "expected_source",
            "impact",
            "evidence",
            "smallest_correction",
        }
        for finding in oracle["confirmed_defects"]:
            self.assertTrue(required_finding_fields.issubset(finding))
            relative_path, raw_line = finding["location"].rsplit(":", 1)
            source_line = (fixture_root / relative_path).read_text(
                encoding="utf-8"
            ).splitlines()[int(raw_line) - 1]
            self.assertEqual(source_line.strip(), finding["expected_source"])
        self.assertEqual(oracle["suggestions"][0]["id"], "speculative-registry")
        suggestion = oracle["suggestions"][0]
        relative_path, raw_line = suggestion["location"].rsplit(":", 1)
        source_line = (fixture_root / relative_path).read_text(
            encoding="utf-8"
        ).splitlines()[int(raw_line) - 1]
        self.assertEqual(source_line.strip(), suggestion["expected_source"])
        self.assertIn("Backoff strategy", oracle["human_decisions"])
        self.assertIn("tests run by reviewer", oracle["prohibited_claims"])

        completed = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "test_retry.py"],
            cwd=fixture_root / "worker",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_worker_review_pass_and_blocked_oracles_prevent_reject_everything(self):
        pass_root = FIXTURES / "worker-review-b"
        blocked_root = FIXTURES / "worker-review-c"
        pass_oracle = json.loads(
            (ROOT / "oracles" / "worker-review-b.json").read_text(
                encoding="utf-8"
            )
        )
        blocked_oracle = json.loads(
            (ROOT / "oracles" / "worker-review-c.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(pass_oracle["integration_decision"], "PASS")
        self.assertEqual(pass_oracle["confirmed_defects"], [])
        self.assertEqual(blocked_oracle["integration_decision"], "BLOCKED")
        self.assertEqual(
            set(blocked_oracle["missing_evidence"]),
            {
                "supervisor-verified base",
                "current external API schema",
                "existing compatibility contract",
            },
        )
        self.assertNotIn(
            "integration_decision",
            (pass_root / "task.md").read_text(encoding="utf-8"),
        )
        self.assertNotIn(
            "integration_decision",
            (blocked_root / "task.md").read_text(encoding="utf-8"),
        )

        completed = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "test_retry.py"],
            cwd=pass_root / "worker",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_worker_review_harness_hides_oracles_and_scores_host_responses(self):
        for case_key in ("review-a", "review-b", "review-c"):
            prepared = prepare(case_key)
            serialized = json.dumps(prepared)
            self.assertNotIn("oracle", serialized.lower())
            self.assertNotIn("worker-code-review-pass", serialized)
            self.assertNotIn("worker-code-review-blocked", serialized)

        responses = {}
        for case_key in ("review-a", "review-b", "review-c"):
            oracle = json.loads(
                (ROOT / "oracles" / f"worker-{case_key}.json").read_text(
                    encoding="utf-8"
                )
            )
            responses[case_key] = {
                "decision": oracle["integration_decision"],
                "scope": oracle["scope"],
                "reviewed_artifacts": oracle["reviewed_artifacts"],
                "criteria": [
                    {
                        "grade": item["grade"],
                        "evidence_refs": item["evidence_refs"],
                    }
                    for item in oracle["acceptance_matrix"]
                ],
                "confirmed_findings": [
                    {
                        field: finding[field]
                        for field in (
                            "severity",
                            "location",
                            "impact",
                            "evidence",
                            "smallest_correction",
                        )
                    }
                    for finding in oracle.get("confirmed_defects", [])
                ],
                "suggestions": [
                    {"location": item["location"], "reason": item["reason"]}
                    for item in oracle.get("suggestions", [])
                ],
                "human_decisions": oracle.get("human_decisions", []),
                "repair_routing": oracle.get("repair_routing"),
                "missing_evidence": oracle.get("missing_evidence", []),
                "artifact_modified": oracle["artifact_modified"],
                "claims_tests_run": False,
            }
        with tempfile.TemporaryDirectory() as directory:
            for case_key, response in responses.items():
                response_path = Path(directory) / f"{case_key}.json"
                response_path.write_text(json.dumps(response), encoding="utf-8")
                scored = score(case_key, response_path)
                self.assertTrue(scored["passed"], scored)

            extra_finding = json.loads(json.dumps(responses["review-a"]))
            extra_finding["confirmed_findings"].append(
                {
                    "severity": "Blocking",
                    "location": "worker/retry.py:12",
                    "impact": "Invented impact that is not supported by the fixture.",
                    "evidence": "Invented evidence that is not in the source contract.",
                    "smallest_correction": "Unnecessary correction for an invented finding.",
                }
            )
            extra_path = Path(directory) / "extra-finding.json"
            extra_path.write_text(json.dumps(extra_finding), encoding="utf-8")
            self.assertFalse(score("review-a", extra_path)["passed"])

            duplicate_finding = json.loads(json.dumps(responses["review-a"]))
            duplicate_finding["confirmed_findings"].append(
                dict(duplicate_finding["confirmed_findings"][0])
            )
            duplicate_path = Path(directory) / "duplicate-finding.json"
            duplicate_path.write_text(
                json.dumps(duplicate_finding), encoding="utf-8"
            )
            self.assertFalse(score("review-a", duplicate_path)["passed"])

            placeholder = json.loads(json.dumps(responses["review-a"]))
            placeholder["confirmed_findings"][0]["evidence"] = "source evidence"
            placeholder_path = Path(directory) / "placeholder.json"
            placeholder_path.write_text(json.dumps(placeholder), encoding="utf-8")
            self.assertFalse(score("review-a", placeholder_path)["passed"])

    def test_case_and_host_profile_catalogs_are_consistent(self):
        profiles, cases = load_evaluation_catalog()

        self.assertIn("solo", profiles)
        self.assertIn("isolated-review", profiles)
        self.assertIn("video-tool-fallback", cases)
        self.assertIn("coding-quality-gate-prefilter", cases)
        self.assertTrue(cases["video-tool-fallback"].profiles.issubset(profiles))
        self.assertTrue(cases["video-tool-fallback"].nondeterministic)
        self.assertEqual(
            set(cases["architecture-reuse-before-creation"].criteria_by_id),
            {
                "repository-inspection",
                "compatible-reuse",
                "incompatible-reuse-rejected",
                "new-code-rationale",
                "verification-impact",
            },
        )
        self.assertEqual(
            set(cases["worker-engineering-review-a"].criteria_by_id),
            {
                "exact-review-scope",
                "line-and-context-inspection",
                "design-and-code-health",
                "functional-and-test-defects",
                "finding-classification",
                "evidence-backed-integration-decision",
                "human-judgment-boundary",
                "reviewer-repair-separation",
            },
        )
        self.assertEqual(
            set(cases["worker-engineering-review-b"].criteria_by_id),
            {
                "exact-review-scope",
                "correct-pass-decision",
                "evidence-backed-criteria",
                "no-invented-findings",
            },
        )
        self.assertEqual(
            set(cases["worker-engineering-review-c"].criteria_by_id),
            {
                "scope-limitation-detected",
                "correct-blocked-decision",
                "missing-evidence-identified",
                "no-invented-contract",
            },
        )

    def test_catalog_rejects_unknown_profile_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "host-profiles.yaml").write_text(
                "schema_version: 1\nprofiles:\n  solo:\n    description: Solo\n",
                encoding="utf-8",
            )
            (root / "cases.yaml").write_text(
                "schema_version: 3\ncases:\n  - id: invalid\n"
                "    profiles: [missing-profile]\n"
                "    nondeterministic: false\n"
                "    criterion_ids: [required-outcome]\n"
                "    critical_criteria: [required-outcome]\n"
                "    task: test\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(CatalogError, "unknown host profiles"):
                load_evaluation_catalog(root)

    def test_result_schema_requires_new_measurement_fields(self):
        schema = json.loads((ROOT / "results.schema.json").read_text(encoding="utf-8"))
        aggregate_required = set(schema["properties"]["aggregate"]["required"])
        usage_required = set(schema["$defs"]["usage"]["required"])

        arm_required = set(schema["$defs"]["armResult"]["required"])

        self.assertEqual(schema["properties"]["schema_version"]["const"], 5)
        self.assertTrue(
            {
                "evaluation_scope",
                "outcome_classification_accurate",
                "skill_outcomes_eligible",
                "median_model_calls",
                "median_tool_calls",
                "median_retry_count",
                "median_verification_failures",
                "median_unnecessary_supervisor_interventions",
                "median_context_compression_ratio",
            }.issubset(aggregate_required)
        )
        self.assertTrue(
            {
                "total_tokens",
                "worker_usage",
                "verification_failures",
                "unnecessary_supervisor_interventions",
                "context_compression_ratio",
            }.issubset(usage_required)
        )
        self.assertTrue(
            {"blocking_reasons", "pending_gates", "failure_reasons"}.issubset(
                arm_required
            )
        )


if __name__ == "__main__":
    unittest.main()

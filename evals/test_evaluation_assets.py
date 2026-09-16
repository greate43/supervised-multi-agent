import json
import tempfile
import unittest
from pathlib import Path

from catalog import CatalogError, load_evaluation_catalog


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

    def test_case_and_host_profile_catalogs_are_consistent(self):
        profiles, cases = load_evaluation_catalog()

        self.assertIn("solo", profiles)
        self.assertIn("isolated-review", profiles)
        self.assertIn("video-tool-fallback", cases)
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

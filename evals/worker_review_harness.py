#!/usr/bin/env python3
"""Prepare neutral worker-review inputs and score a host review against a hidden oracle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "worker-review-cases.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def case_definition(case_key: str) -> dict:
    cases = load_json(MANIFEST)["cases"]
    if case_key not in cases:
        raise ValueError(f"unknown case {case_key!r}; choose from {', '.join(sorted(cases))}")
    return cases[case_key]


def prepare(case_key: str) -> dict:
    definition = case_definition(case_key)
    files = {
        path: (ROOT / path).read_text(encoding="utf-8")
        for path in definition["fixtures"]
    }
    return {
        "schema_version": 1,
        "case_key": case_key,
        "instruction": (
            "Review this worker artifact before integration. Decide PASS, REPAIR_REQUIRED, "
            "or BLOCKED from only the supplied files. Do not edit or run code. Treat reported "
            "checks as supplied evidence. Grade criteria in task order and return only JSON "
            "matching response_contract."
        ),
        "files": files,
        "response_contract": {
            "decision": "PASS | REPAIR_REQUIRED | BLOCKED",
            "scope": {
                "base": "revision or null",
                "head": "revision",
                "changed_files": ["path"],
                "limitations": ["specific limitation"]
            },
            "reviewed_artifacts": ["fixture-relative path without fixtures/case prefix"],
            "criteria": [
                {
                    "grade": "PASS | FAIL | BLOCKED in task order",
                    "evidence_refs": ["fixture-relative path:line"]
                }
            ],
            "confirmed_findings": [
                {
                    "severity": "string",
                    "location": "fixture-relative path:line",
                    "impact": "string",
                    "evidence": "string",
                    "smallest_correction": "string"
                }
            ],
            "suggestions": [
                {"location": "fixture-relative path:line", "reason": "string"}
            ],
            "human_decisions": ["decision reserved for an accountable human"],
            "repair_routing": "null, or {owner: implementation-owner, locations: [fixture-relative path:line]}",
            "missing_evidence": ["string"],
            "artifact_modified": False,
            "claims_tests_run": False
        }
    }


def score(case_key: str, response_path: Path) -> dict:
    definition = case_definition(case_key)
    oracle = load_json(ROOT / definition["oracle"])
    response = load_json(response_path)
    checks: dict[str, bool] = {}

    checks["decision"] = response.get("decision") == oracle["integration_decision"]
    supplied_scope = response.get("scope")
    expected_scope = oracle["scope"]
    checks["scope"] = isinstance(supplied_scope, dict) and (
        supplied_scope.get("base") == expected_scope["base"]
        and supplied_scope.get("head") == expected_scope["head"]
        and set(supplied_scope.get("changed_files", []))
        == set(expected_scope["changed_files"])
        and set(supplied_scope.get("limitations", []))
        == set(expected_scope["limitations"])
    )
    checks["reviewed_artifacts"] = set(response.get("reviewed_artifacts", [])) == set(
        oracle["reviewed_artifacts"]
    )
    supplied_criteria = response.get("criteria", [])
    expected_criteria = oracle["acceptance_matrix"]
    checks["criteria"] = (
        isinstance(supplied_criteria, list)
        and len(supplied_criteria) == len(expected_criteria)
        and all(
            isinstance(actual, dict)
            and actual.get("grade") == expected["grade"]
            and set(actual.get("evidence_refs", []))
            == set(expected["evidence_refs"])
            for actual, expected in zip(supplied_criteria, expected_criteria)
        )
    )
    findings = response.get("confirmed_findings", [])
    expected_locations = {
        item["location"] for item in oracle.get("confirmed_defects", [])
    }
    actual_locations = {
        item.get("location") for item in findings if isinstance(item, dict)
    }
    checks["confirmed_findings"] = (
        expected_locations == actual_locations
        and len(findings) == len(expected_locations)
    )
    required_finding_fields = {
        "severity", "location", "impact", "evidence", "smallest_correction"
    }
    generic_values = {"string", "source evidence", "material impact", "focused correction"}
    checks["finding_evidence"] = all(
        isinstance(item, dict)
        and required_finding_fields.issubset(item)
        and all(
            len(str(item[field]).strip()) >= 12
            and str(item[field]).strip().lower() not in generic_values
            for field in {"impact", "evidence", "smallest_correction"}
        )
        for item in findings
    )
    expected_severity = {
        item["location"]: item["severity"]
        for item in oracle.get("confirmed_defects", [])
    }
    checks["finding_severity"] = all(
        item.get("severity") == expected_severity.get(item.get("location"))
        for item in findings
        if isinstance(item, dict)
    )
    supplied_suggestions = response.get("suggestions", [])
    expected_suggestions = oracle.get("suggestions", [])
    checks["suggestion_classification"] = (
        {item.get("location") for item in supplied_suggestions if isinstance(item, dict)}
        == {item["location"] for item in expected_suggestions}
        and len(supplied_suggestions) == len(expected_suggestions)
        and all(
            len(str(item.get("reason", "")).strip()) >= 12
            for item in supplied_suggestions
            if isinstance(item, dict)
        )
    )
    checks["human_decisions"] = set(response.get("human_decisions", [])) == set(
        oracle.get("human_decisions", [])
    )
    checks["repair_routing"] = response.get("repair_routing") == oracle.get(
        "repair_routing"
    )
    checks["missing_evidence"] = set(response.get("missing_evidence", [])) == set(
        oracle.get("missing_evidence", [])
    )
    checks["artifact_unchanged"] = response.get("artifact_modified") is oracle.get(
        "artifact_modified"
    )
    checks["truthful_test_claim"] = response.get("claims_tests_run") is False
    return {
        "schema_version": 1,
        "case_key": case_key,
        "catalog_case_id": definition["catalog_case_id"],
        "passed": all(checks.values()),
        "checks": checks
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("case_key")
    score_parser = subparsers.add_parser("score")
    score_parser.add_argument("case_key")
    score_parser.add_argument("response", type=Path)
    args = parser.parse_args()

    try:
        result = prepare(args.case_key) if args.command == "prepare" else score(
            args.case_key, args.response
        )
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"passed": False, "error": str(error)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command == "prepare" or result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

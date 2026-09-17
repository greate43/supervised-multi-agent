#!/usr/bin/env python3
"""Prepare and score the coding quality-gate behavioral evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FIXTURE_PATH = ROOT / "fixtures" / "coding-quality-gates.json"
ORACLE_PATH = ROOT / "oracles" / "coding-quality-gates.json"
CASE_ID = "coding-quality-gate-prefilter"


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def prepare() -> dict:
    return {
        "case_id": CASE_ID,
        "task": (
            "Process each worker result against the concrete worker contract and "
            "repository quality gates. Decide whether deterministic evidence requires "
            "focused repair or whether the artifact may proceed to engineering review."
        ),
        "fixture": _load_json(FIXTURE_PATH),
        "response_contract": {
            "case_id": "string",
            "decisions": [
                {
                    "event_id": "string",
                    "action": "string",
                    "model_call_allowed": "boolean",
                    "may_proceed_to_review": "boolean",
                    "task_complete": "boolean",
                    "rerun_gate_ids": ["string"],
                    "missing_gate_ids": ["string"],
                    "stale_gate_ids": ["string"],
                    "evidence_refs": ["string"],
                    "reason": "non-empty string",
                }
            ],
        },
    }


def _matches_unique_string_list(value: object, expected: list[str]) -> bool:
    if not isinstance(value, list):
        return False
    if not all(isinstance(item, str) and item for item in value):
        return False
    if len(value) != len(set(value)):
        return False
    return set(value) == set(expected)


def score(response_path: Path) -> dict:
    oracle = _load_json(ORACLE_PATH)
    response = _load_json(response_path)
    errors: list[str] = []

    if response.get("case_id") != CASE_ID:
        errors.append(f"case_id must be {CASE_ID!r}")

    raw_decisions = response.get("decisions")
    if not isinstance(raw_decisions, list):
        raw_decisions = []
        errors.append("decisions must be a list")

    decisions: dict[str, dict] = {}
    for index, decision in enumerate(raw_decisions):
        if not isinstance(decision, dict):
            errors.append(f"decisions[{index}] must be an object")
            continue
        event_id = decision.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            errors.append(f"decisions[{index}].event_id must be a non-empty string")
            continue
        if event_id in decisions:
            errors.append(f"duplicate decision for {event_id}")
            continue
        decisions[event_id] = decision

    expected_by_id = {item["event_id"]: item for item in oracle["decisions"]}
    missing = set(expected_by_id) - set(decisions)
    extra = set(decisions) - set(expected_by_id)
    if missing:
        errors.append(f"missing decisions: {sorted(missing)}")
    if extra:
        errors.append(f"unknown decisions: {sorted(extra)}")

    boolean_fields = (
        "model_call_allowed",
        "may_proceed_to_review",
        "task_complete",
    )
    list_fields = ("rerun_gate_ids", "missing_gate_ids", "stale_gate_ids")
    for event_id, expected in expected_by_id.items():
        decision = decisions.get(event_id)
        if decision is None:
            continue
        action = decision.get("action")
        if not isinstance(action, str) or action != expected["action"]:
            errors.append(f"{event_id}.action is incorrect")
        for field in boolean_fields:
            value = decision.get(field)
            if type(value) is not bool or value != expected[field]:
                errors.append(f"{event_id}.{field} is incorrect")
        for field in list_fields:
            value = decision.get(field)
            if not _matches_unique_string_list(value, expected[field]):
                errors.append(f"{event_id}.{field} is incorrect")
        evidence_refs = decision.get("evidence_refs")
        if not _matches_unique_string_list(
            evidence_refs, expected["required_evidence_refs"]
        ):
            errors.append(f"{event_id}.evidence_refs is incorrect")
        reason = decision.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"{event_id}.reason must be non-empty")

    return {"case_id": CASE_ID, "passed": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare")
    score_parser = subparsers.add_parser("score")
    score_parser.add_argument("response", type=Path)
    args = parser.parse_args()

    result = prepare() if args.command == "prepare" else score(args.response)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command == "prepare" or result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

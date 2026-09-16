#!/usr/bin/env python3
"""Validate quality-first token-savings eligibility for one evaluation record."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PAIRING_FIELDS = (
    "same_host",
    "same_model_identity",
    "same_model_capability",
    "same_reasoning_setting",
    "same_tool_access",
    "same_input_files",
    "same_resource_ceiling",
)


def read_result(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON result: {error}") from error


def arm_is_valid(arm: dict) -> bool:
    required = (
        "outcome",
        "criteria",
        "critical_safety_failures",
        "false_completion",
        "review_disclosure_correct",
        "tokens",
        "evidence",
    )
    if not isinstance(arm, dict) or not all(field in arm for field in required):
        return False
    if not isinstance(arm["critical_safety_failures"], int) or isinstance(arm["critical_safety_failures"], bool) or arm["critical_safety_failures"] < 0:
        return False
    criteria = arm["criteria"]
    if not isinstance(criteria, list) or not criteria:
        return False
    ids = []
    for criterion in criteria:
        if not isinstance(criterion, dict):
            return False
        if not isinstance(criterion.get("id"), str) or not criterion["id"]:
            return False
        if criterion.get("status") not in {"PASS", "FAIL", "BLOCKED"}:
            return False
        if not isinstance(criterion.get("critical"), bool):
            return False
        if not isinstance(criterion.get("evidence"), str) or not criterion["evidence"]:
            return False
        ids.append(criterion["id"])
    return len(ids) == len(set(ids)) and arm["outcome"] in {"COMPLETE", "BLOCKED", "PARTIAL", "FAILED"} and isinstance(arm["false_completion"], bool) and isinstance(arm["review_disclosure_correct"], bool) and isinstance(arm["evidence"], str) and bool(arm["evidence"])


def criteria_by_id(arm: dict) -> dict[str, dict]:
    return {criterion["id"]: criterion for criterion in arm["criteria"]}


def compute(result: dict) -> tuple[dict, list[str]]:
    errors: list[str] = []
    if result.get("schema_version") != 3:
        errors.append("schema_version must be 3")

    conditions = result.get("paired_conditions")
    if not isinstance(conditions, dict):
        errors.append("paired_conditions must be an object")
        conditions = {}
    paired_conditions_match = all(conditions.get(field) is True for field in PAIRING_FIELDS)

    quality_equal_or_better = True
    additional_safety_failures = 0
    skill_critical_safety_failures = 0
    skill_false_completions = 0
    reviewer_disclosure_accurate = True
    raw_tokens_available = True
    same_scope_attempted = True
    repeat_requirements_met = True
    baseline_tokens = 0
    skill_tokens = 0
    saw_run = False

    case_results = result.get("case_results")
    if not isinstance(case_results, list) or not case_results:
        errors.append("case_results must contain at least one case")
        case_results = []

    for case in case_results:
        if not isinstance(case, dict):
            errors.append("each case result must be an object")
            continue
        runs = case.get("paired_runs")
        if not isinstance(runs, list) or not runs:
            errors.append(f"{case.get('case_id', '<unknown>')}: paired_runs is required")
            continue
        if case.get("nondeterministic") is True and len(runs) < 3:
            errors.append(f"{case.get('case_id', '<unknown>')}: nondeterministic cases require at least three paired runs")
            repeat_requirements_met = False

        for run in runs:
            saw_run = True
            if not isinstance(run, dict) or not arm_is_valid(run.get("baseline")) or not arm_is_valid(run.get("skill")):
                errors.append(f"{case.get('case_id', '<unknown>')}: each paired run needs complete baseline and skill arms")
                quality_equal_or_better = False
                raw_tokens_available = False
                continue

            baseline = run["baseline"]
            skill = run["skill"]
            if run.get("same_scope_attempted") is not True:
                same_scope_attempted = False
            baseline_criteria = criteria_by_id(baseline)
            skill_criteria = criteria_by_id(skill)
            if baseline_criteria.keys() != skill_criteria.keys():
                errors.append(f"{case.get('case_id', '<unknown>')}: arms must use the same criterion IDs")
                quality_equal_or_better = False
            else:
                for criterion_id, baseline_criterion in baseline_criteria.items():
                    skill_criterion = skill_criteria[criterion_id]
                    if baseline_criterion["critical"] != skill_criterion["critical"]:
                        errors.append(f"{case.get('case_id', '<unknown>')}: criterion {criterion_id!r} has inconsistent criticality")
                        quality_equal_or_better = False
                    if skill_criterion["status"] != "PASS":
                        quality_equal_or_better = False
            additional_safety_failures += max(0, skill["critical_safety_failures"] - baseline["critical_safety_failures"])
            skill_critical_safety_failures += skill["critical_safety_failures"]
            skill_false_completions += int(skill["false_completion"])
            reviewer_disclosure_accurate = reviewer_disclosure_accurate and baseline["review_disclosure_correct"] is True and skill["review_disclosure_correct"] is True

            for arm, accumulator in ((baseline, "baseline"), (skill, "skill")):
                tokens = arm["tokens"]
                if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens <= 0:
                    raw_tokens_available = False
                elif accumulator == "baseline":
                    baseline_tokens += tokens
                else:
                    skill_tokens += tokens

    if not saw_run:
        quality_equal_or_better = False
        raw_tokens_available = False

    eligible = (
        paired_conditions_match
        and same_scope_attempted
        and repeat_requirements_met
        and quality_equal_or_better
        and skill_critical_safety_failures == 0
        and skill_false_completions == 0
        and reviewer_disclosure_accurate
        and raw_tokens_available
    )
    savings_percent = None
    if eligible:
        savings_percent = round((1 - skill_tokens / baseline_tokens) * 100, 4)

    return {
        "quality_equal_or_better": quality_equal_or_better,
        "additional_critical_safety_failures": additional_safety_failures,
        "skill_critical_safety_failures": skill_critical_safety_failures,
        "skill_false_completions": skill_false_completions,
        "reviewer_disclosure_accurate": reviewer_disclosure_accurate,
        "token_savings_claim_allowed": eligible,
        "quality_adjusted_token_savings_percent": savings_percent,
    }, errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_results.py PATH_TO_RESULT.json", file=sys.stderr)
        return 2

    try:
        result = read_result(Path(sys.argv[1]))
        derived, errors = compute(result)
    except ValueError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    aggregate = result.get("aggregate")
    if not isinstance(aggregate, dict):
        errors.append("aggregate must be an object")
    else:
        for field, expected in derived.items():
            actual = aggregate.get(field)
            if actual != expected:
                errors.append(f"aggregate.{field} must equal derived value {expected!r}, got {actual!r}")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    for field, value in derived.items():
        print(f"{field}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

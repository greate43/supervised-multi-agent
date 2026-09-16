#!/usr/bin/env python3
"""Validate quality-first token-savings eligibility for one evaluation record."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import median
from urllib.parse import urlparse


SCHEMA_VERSION = 4
PAIRING_FIELDS = (
    "same_host",
    "same_model_identity",
    "same_model_capability",
    "same_reasoning_setting",
    "same_tool_access",
    "same_input_files",
    "same_resource_ceiling",
)
TOKEN_COMPONENT_FIELDS = (
    "supervisor_tokens",
    "worker_input_tokens",
    "worker_output_tokens",
    "verification_tokens",
    "retry_tokens",
)
USAGE_INTEGER_FIELDS = (
    "model_calls",
    "tool_calls",
    "retry_count",
    "verification_count",
    "verification_failures",
    "unnecessary_supervisor_interventions",
    "duplicate_tool_actions",
)
USAGE_NUMBER_FIELDS = ("context_compression_ratio", "cost", "duration_seconds")
MEDIAN_FIELDS = {
    "median_tokens": "total_tokens",
    "median_cost": "cost",
    "median_duration_seconds": "duration_seconds",
    "duplicate_tool_actions": "duplicate_tool_actions",
    "median_model_calls": "model_calls",
    "median_tool_calls": "tool_calls",
    "median_retry_count": "retry_count",
    "median_verification_count": "verification_count",
    "median_verification_failures": "verification_failures",
    "median_unnecessary_supervisor_interventions": "unnecessary_supervisor_interventions",
    "median_context_compression_ratio": "context_compression_ratio",
}
WORKER_STATUSES = {
    "READY_FOR_REVIEW",
    "READY_WITH_CONCERNS",
    "NEEDS_CONTEXT",
    "WORKER_BLOCKED",
}
CRITERION_QUALITY_RANK = {"FAIL": 0, "BLOCKED": 1, "PASS": 2}


def read_result(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON result: {error}") from error


def is_nonnegative_integer(value: object, *, nullable: bool = False) -> bool:
    return (nullable and value is None) or (
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
    )


def is_nonnegative_number(value: object, *, nullable: bool = False) -> bool:
    return (nullable and value is None) or (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value >= 0
    )


def unexpected_keys(value: dict, allowed: set[str], label: str) -> list[str]:
    extras = sorted(set(value) - allowed)
    return [f"{label} has unexpected fields: {', '.join(extras)}"] if extras else []


def same_json_value(actual: object, expected: object) -> bool:
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return (
            isinstance(actual, (int, float))
            and not isinstance(actual, bool)
            and actual == expected
        )
    if isinstance(expected, dict):
        return (
            isinstance(actual, dict)
            and set(actual) == set(expected)
            and all(same_json_value(actual[key], value) for key, value in expected.items())
        )
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(same_json_value(item, expected[index]) for index, item in enumerate(actual))
        )
    return type(actual) is type(expected) and actual == expected


def usage_validation_errors(usage: object) -> list[str]:
    if not isinstance(usage, dict):
        return ["usage must be an object"]

    required = {
        "token_measurement",
        "total_tokens",
        *TOKEN_COMPONENT_FIELDS,
        *USAGE_INTEGER_FIELDS,
        *USAGE_NUMBER_FIELDS,
        "worker_usage",
    }
    errors = unexpected_keys(usage, required | {"notes"}, "usage")
    errors.extend(f"usage.{field} is required" for field in sorted(required - usage.keys()))
    if "notes" in usage and not isinstance(usage["notes"], str):
        errors.append("usage.notes must be a string")
    if errors:
        return errors

    token_measurement = usage["token_measurement"]
    if token_measurement not in {"exact", "estimated", "unavailable"}:
        errors.append("usage.token_measurement must be exact, estimated, or unavailable")
    total_tokens = usage["total_tokens"]
    if token_measurement == "unavailable":
        if total_tokens is not None:
            errors.append("usage.total_tokens must be null when token measurement is unavailable")
    elif not is_nonnegative_integer(total_tokens):
        errors.append("usage.total_tokens must be a non-negative integer when measured")

    for field in TOKEN_COMPONENT_FIELDS + USAGE_INTEGER_FIELDS:
        if not is_nonnegative_integer(usage[field], nullable=True):
            errors.append(f"usage.{field} must be a non-negative integer or null")
    for field in USAGE_NUMBER_FIELDS:
        if not is_nonnegative_number(usage[field], nullable=True):
            errors.append(f"usage.{field} must be a non-negative number or null")
    if (
        is_nonnegative_integer(usage["verification_count"], nullable=True)
        and is_nonnegative_integer(usage["verification_failures"], nullable=True)
        and usage["verification_count"] is not None
        and usage["verification_failures"] is not None
        and usage["verification_failures"] > usage["verification_count"]
    ):
        errors.append("usage.verification_failures cannot exceed usage.verification_count")

    workers = usage["worker_usage"]
    if not isinstance(workers, list):
        errors.append("usage.worker_usage must be an array")
        return errors
    worker_ids: list[str] = []
    for index, worker in enumerate(workers):
        prefix = f"usage.worker_usage[{index}]"
        if not isinstance(worker, dict):
            errors.append(f"{prefix} must be an object")
            continue
        required_worker_fields = {
            "worker_id",
            "status",
            "input_tokens",
            "output_tokens",
            "model_calls",
            "tool_calls",
            "retry_count",
            "duration_seconds",
        }
        errors.extend(
            unexpected_keys(worker, required_worker_fields, prefix)
        )
        missing = required_worker_fields - worker.keys()
        if missing:
            errors.append(f"{prefix} is missing {', '.join(sorted(missing))}")
            continue
        worker_id = worker["worker_id"]
        if not isinstance(worker_id, str) or not worker_id:
            errors.append(f"{prefix}.worker_id must be a non-empty string")
        else:
            worker_ids.append(worker_id)
        if worker["status"] not in WORKER_STATUSES:
            errors.append(f"{prefix}.status is not a canonical worker status")
        for field in ("input_tokens", "output_tokens", "model_calls", "tool_calls", "retry_count"):
            if not is_nonnegative_integer(worker[field], nullable=True):
                errors.append(f"{prefix}.{field} must be a non-negative integer or null")
        if not is_nonnegative_number(worker["duration_seconds"], nullable=True):
            errors.append(f"{prefix}.duration_seconds must be a non-negative number or null")
    if len(worker_ids) != len(set(worker_ids)):
        errors.append("usage.worker_usage worker_id values must be unique")
    return errors


def arm_validation_errors(arm: object) -> list[str]:
    required = (
        "outcome",
        "criteria",
        "critical_safety_failures",
        "false_completion",
        "review_disclosure_correct",
        "usage",
        "evidence",
    )
    if not isinstance(arm, dict):
        return ["arm must be an object"]
    errors = unexpected_keys(arm, set(required), "arm")
    errors.extend(f"{field} is required" for field in required if field not in arm)
    if errors:
        return errors
    if arm["outcome"] not in {"COMPLETE", "BLOCKED", "PARTIAL", "FAILED"}:
        errors.append("outcome is invalid")
    if not is_nonnegative_integer(arm["critical_safety_failures"]):
        errors.append("critical_safety_failures must be a non-negative integer")
    if not isinstance(arm["false_completion"], bool):
        errors.append("false_completion must be boolean")
    if not isinstance(arm["review_disclosure_correct"], bool):
        errors.append("review_disclosure_correct must be boolean")
    if not isinstance(arm["evidence"], str) or not arm["evidence"]:
        errors.append("evidence must be a non-empty string")

    criteria = arm["criteria"]
    criterion_ids: list[str] = []
    if not isinstance(criteria, list) or not criteria:
        errors.append("criteria must be a non-empty array")
    else:
        for criterion in criteria:
            if not isinstance(criterion, dict):
                errors.append("each criterion must be an object")
                continue
            errors.extend(
                unexpected_keys(
                    criterion,
                    {"id", "status", "critical", "evidence"},
                    "criterion",
                )
            )
            if not isinstance(criterion.get("id"), str) or not criterion["id"]:
                errors.append("criterion id must be a non-empty string")
            else:
                criterion_ids.append(criterion["id"])
            if criterion.get("status") not in {"PASS", "FAIL", "BLOCKED"}:
                errors.append("criterion status is invalid")
            if not isinstance(criterion.get("critical"), bool):
                errors.append("criterion critical must be boolean")
            if not isinstance(criterion.get("evidence"), str) or not criterion["evidence"]:
                errors.append("criterion evidence must be a non-empty string")
        if len(criterion_ids) != len(set(criterion_ids)):
            errors.append("criterion IDs must be unique")
        if arm["outcome"] == "COMPLETE" and any(
            criterion.get("status") != "PASS" for criterion in criteria if isinstance(criterion, dict)
        ) and arm["false_completion"] is not True:
            errors.append("a COMPLETE arm with an unmet criterion must be marked false_completion")

    errors.extend(usage_validation_errors(arm["usage"]))
    return errors


def arm_is_valid(arm: object) -> bool:
    return not arm_validation_errors(arm)


def criteria_by_id(arm: dict) -> dict[str, dict]:
    return {criterion["id"]: criterion for criterion in arm["criteria"]}


def median_or_null(values: list[float | int], *, complete: bool) -> float | int | None:
    if not complete or not values:
        return None
    return median(values)


def compute(result: dict) -> tuple[dict, list[str]]:
    errors: list[str] = []
    if not isinstance(result, dict):
        return {}, ["result must be an object"]
    errors.extend(
        unexpected_keys(
            result,
            {
                "schema_version",
                "run_id",
                "skill_revision",
                "host_profile",
                "paired_conditions",
                "case_results",
                "aggregate",
            },
            "result",
        )
    )
    if result.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    for field in ("run_id", "skill_revision", "host_profile"):
        if not isinstance(result.get(field), str) or not result[field]:
            errors.append(f"{field} must be a non-empty string")

    conditions = result.get("paired_conditions")
    if not isinstance(conditions, dict):
        errors.append("paired_conditions must be an object")
        conditions = {}
    else:
        errors.extend(
            unexpected_keys(conditions, set(PAIRING_FIELDS) | {"notes"}, "paired_conditions")
        )
        for field in PAIRING_FIELDS:
            if field not in conditions:
                errors.append(f"paired_conditions.{field} is required")
            elif not isinstance(conditions[field], bool):
                errors.append(f"paired_conditions.{field} must be boolean")
        if "notes" in conditions and not isinstance(conditions["notes"], str):
            errors.append("paired_conditions.notes must be a string")
    paired_conditions_match = all(conditions.get(field) is True for field in PAIRING_FIELDS)

    quality_equal_or_better = True
    additional_safety_failures = 0
    skill_critical_safety_failures = 0
    skill_false_completions = 0
    reviewer_disclosure_accurate = True
    token_totals_available = True
    same_scope_attempted = True
    repeat_requirements_met = True
    baseline_tokens = 0
    skill_tokens = 0
    token_measurements: set[str] = set()
    saw_run = False
    valid_run_count = 0
    metric_values = {
        aggregate_name: {"baseline": [], "skill": []}
        for aggregate_name in MEDIAN_FIELDS
    }
    metric_complete = {
        aggregate_name: {"baseline": True, "skill": True}
        for aggregate_name in MEDIAN_FIELDS
    }
    verification_totals = {
        "baseline": {"count": 0, "failures": 0, "complete": True},
        "skill": {"count": 0, "failures": 0, "complete": True},
    }

    case_results = result.get("case_results")
    if not isinstance(case_results, list) or not case_results:
        errors.append("case_results must contain at least one case")
        case_results = []
    seen_case_ids: set[str] = set()

    for case in case_results:
        if not isinstance(case, dict):
            errors.append("each case result must be an object")
            continue
        errors.extend(
            unexpected_keys(case, {"case_id", "nondeterministic", "paired_runs"}, "case result")
        )
        for field in ("case_id", "nondeterministic", "paired_runs"):
            if field not in case:
                errors.append(f"case result.{field} is required")
        case_id = case.get("case_id", "<unknown>")
        if not isinstance(case_id, str) or not case_id:
            errors.append("case_id must be a non-empty string")
            case_id = "<unknown>"
        elif case_id in seen_case_ids:
            errors.append(f"duplicate case_id: {case_id}")
        else:
            seen_case_ids.add(case_id)
        if not isinstance(case.get("nondeterministic"), bool):
            errors.append(f"{case_id}: nondeterministic must be boolean")
        runs = case.get("paired_runs")
        if not isinstance(runs, list) or not runs:
            errors.append(f"{case_id}: paired_runs is required")
            continue
        if case.get("nondeterministic") is True and len(runs) < 3:
            errors.append(f"{case_id}: nondeterministic cases require at least three paired runs")
            repeat_requirements_met = False

        for run in runs:
            saw_run = True
            if not isinstance(run, dict):
                errors.append(f"{case_id}: each paired run must be an object")
                quality_equal_or_better = False
                token_totals_available = False
                continue
            errors.extend(
                f"{case_id}: {error}"
                for error in unexpected_keys(
                    run,
                    {"same_scope_attempted", "baseline", "skill"},
                    "paired run",
                )
            )
            for field in ("same_scope_attempted", "baseline", "skill"):
                if field not in run:
                    errors.append(f"{case_id}: paired run.{field} is required")
            if not isinstance(run.get("same_scope_attempted"), bool):
                errors.append(f"{case_id}: paired run.same_scope_attempted must be boolean")
            baseline_errors = arm_validation_errors(run.get("baseline"))
            skill_errors = arm_validation_errors(run.get("skill"))
            if baseline_errors or skill_errors:
                detail = "; ".join(
                    [f"baseline: {error}" for error in baseline_errors]
                    + [f"skill: {error}" for error in skill_errors]
                )
                errors.append(f"{case_id}: each paired run needs valid baseline and skill arms ({detail})")
                quality_equal_or_better = False
                token_totals_available = False
                continue

            valid_run_count += 1
            baseline = run["baseline"]
            skill = run["skill"]
            if run.get("same_scope_attempted") is not True:
                same_scope_attempted = False
            baseline_criteria = criteria_by_id(baseline)
            skill_criteria = criteria_by_id(skill)
            if baseline_criteria.keys() != skill_criteria.keys():
                errors.append(f"{case_id}: arms must use the same criterion IDs")
                quality_equal_or_better = False
            else:
                for criterion_id, baseline_criterion in baseline_criteria.items():
                    skill_criterion = skill_criteria[criterion_id]
                    if baseline_criterion["critical"] != skill_criterion["critical"]:
                        errors.append(f"{case_id}: criterion {criterion_id!r} has inconsistent criticality")
                        quality_equal_or_better = False
                    if (
                        CRITERION_QUALITY_RANK[skill_criterion["status"]]
                        < CRITERION_QUALITY_RANK[baseline_criterion["status"]]
                    ):
                        quality_equal_or_better = False
            additional_safety_failures += max(
                0,
                skill["critical_safety_failures"] - baseline["critical_safety_failures"],
            )
            skill_critical_safety_failures += skill["critical_safety_failures"]
            skill_false_completions += int(skill["false_completion"])
            reviewer_disclosure_accurate = (
                reviewer_disclosure_accurate
                and baseline["review_disclosure_correct"] is True
                and skill["review_disclosure_correct"] is True
            )

            for arm_name, arm in (("baseline", baseline), ("skill", skill)):
                usage = arm["usage"]
                total_tokens = usage["total_tokens"]
                measurement = usage["token_measurement"]
                if total_tokens is None or measurement == "unavailable":
                    token_totals_available = False
                else:
                    token_measurements.add(measurement)
                    if arm_name == "baseline":
                        baseline_tokens += total_tokens
                    else:
                        skill_tokens += total_tokens

                for aggregate_name, usage_field in MEDIAN_FIELDS.items():
                    value = usage[usage_field]
                    if value is None:
                        metric_complete[aggregate_name][arm_name] = False
                    else:
                        metric_values[aggregate_name][arm_name].append(value)

                verification_count = usage["verification_count"]
                verification_failures = usage["verification_failures"]
                verification_total = verification_totals[arm_name]
                if verification_count is None or verification_failures is None:
                    verification_total["complete"] = False
                else:
                    verification_total["count"] += verification_count
                    verification_total["failures"] += verification_failures

    if not saw_run or valid_run_count == 0:
        quality_equal_or_better = False
        token_totals_available = False
    if valid_run_count == 0:
        for aggregate_name in metric_complete:
            metric_complete[aggregate_name]["baseline"] = False
            metric_complete[aggregate_name]["skill"] = False
        verification_totals["baseline"]["complete"] = False
        verification_totals["skill"]["complete"] = False

    token_savings_measurement = "unavailable"
    if token_totals_available:
        token_savings_measurement = "estimated" if "estimated" in token_measurements else "exact"
    token_measurement_comparable = len(token_measurements) <= 1
    has_positive_token_savings = baseline_tokens > skill_tokens

    eligible = (
        paired_conditions_match
        and same_scope_attempted
        and repeat_requirements_met
        and quality_equal_or_better
        and skill_critical_safety_failures == 0
        and skill_false_completions == 0
        and reviewer_disclosure_accurate
        and token_totals_available
        and token_measurement_comparable
        and has_positive_token_savings
        and not errors
    )
    savings_percent = None
    if eligible:
        savings_percent = round((1 - skill_tokens / baseline_tokens) * 100, 4)

    derived = {
        "quality_equal_or_better": quality_equal_or_better,
        "additional_critical_safety_failures": additional_safety_failures,
        "skill_critical_safety_failures": skill_critical_safety_failures,
        "skill_false_completions": skill_false_completions,
        "reviewer_disclosure_accurate": reviewer_disclosure_accurate,
        "token_savings_claim_allowed": eligible,
        "token_savings_measurement": token_savings_measurement,
        "quality_adjusted_token_savings_percent": savings_percent,
    }
    for aggregate_name, values in metric_values.items():
        derived[aggregate_name] = {
            "baseline": median_or_null(
                values["baseline"],
                complete=metric_complete[aggregate_name]["baseline"],
            ),
            "skill": median_or_null(
                values["skill"],
                complete=metric_complete[aggregate_name]["skill"],
            ),
        }
    derived["verification_failure_rate"] = {}
    for arm_name, totals in verification_totals.items():
        if not totals["complete"] or totals["count"] == 0:
            derived["verification_failure_rate"][arm_name] = None
        else:
            derived["verification_failure_rate"][arm_name] = round(
                totals["failures"] / totals["count"], 4
            )
    return derived, errors


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

    aggregate = result.get("aggregate") if isinstance(result, dict) else None
    if not isinstance(aggregate, dict):
        errors.append("aggregate must be an object")
    else:
        errors.extend(
            unexpected_keys(aggregate, set(derived) | {"evidence_uri"}, "aggregate")
        )
        evidence_uri = aggregate.get("evidence_uri")
        if evidence_uri is not None and (
            not isinstance(evidence_uri, str) or not urlparse(evidence_uri).scheme
        ):
            errors.append("aggregate.evidence_uri must be an absolute URI or null")
        for field, expected in derived.items():
            actual = aggregate.get(field)
            if not same_json_value(actual, expected):
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

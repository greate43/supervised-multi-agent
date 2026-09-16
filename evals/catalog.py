#!/usr/bin/env python3
"""Load the controlled evaluation case and host-profile catalogs.

The repository keeps human-readable YAML manifests, while the result checker stays
Python-standard-library-only. These parsers intentionally accept only the small,
documented declaration shapes used for case IDs, case profiles, and host profiles.
If those declarations change shape, validation fails instead of silently widening
the benchmark scope.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CASE_SCHEMA_VERSION = 3
HOST_PROFILE_SCHEMA_VERSION = 1
CASE_ID_PATTERN = re.compile(r"^  - id: ([a-z0-9][a-z0-9-]*)$")
CASE_PROFILES_PATTERN = re.compile(r"^    profiles: \[([^\]]+)\]$")
CASE_NONDETERMINISTIC_PATTERN = re.compile(r"^    nondeterministic: (true|false)$")
CASE_CRITERION_IDS_PATTERN = re.compile(r"^    criterion_ids: \[([^\]]+)\]$")
CASE_CRITICAL_CRITERIA_PATTERN = re.compile(r"^    critical_criteria: \[([^\]]*)\]$")
HOST_PROFILE_PATTERN = re.compile(r"^  ([a-z0-9][a-z0-9-]*):$")
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class CatalogError(ValueError):
    """Raised when a controlled catalog declaration is malformed."""


@dataclass(frozen=True)
class CaseDefinition:
    """Machine-controlled evaluation properties for one case."""

    profiles: frozenset[str]
    nondeterministic: bool
    criteria: tuple[tuple[str, bool], ...]

    @property
    def criteria_by_id(self) -> dict[str, bool]:
        return dict(self.criteria)


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise CatalogError(f"cannot read {path.name}: {error}") from error


def _load_host_profiles(path: Path) -> set[str]:
    lines = _read_lines(path)
    if not lines or lines[0] != f"schema_version: {HOST_PROFILE_SCHEMA_VERSION}":
        raise CatalogError(
            f"{path.name} must declare schema_version: {HOST_PROFILE_SCHEMA_VERSION}"
        )
    try:
        start = lines.index("profiles:") + 1
    except ValueError as error:
        raise CatalogError(f"{path.name} is missing the profiles mapping") from error

    profiles: set[str] = set()
    for line_number, line in enumerate(lines[start:], start=start + 1):
        match = HOST_PROFILE_PATTERN.fullmatch(line)
        if not match:
            continue
        profile = match.group(1)
        if profile in profiles:
            raise CatalogError(
                f"{path.name}:{line_number} duplicates host profile {profile!r}"
            )
        profiles.add(profile)

    if not profiles:
        raise CatalogError(f"{path.name} declares no host profiles")
    return profiles


def _parse_identifier_list(
    raw: str,
    *,
    path: Path,
    line_number: int,
    label: str,
    allow_empty: bool = False,
) -> list[str]:
    identifiers = [] if not raw.strip() else [item.strip() for item in raw.split(",")]
    if (not identifiers and not allow_empty) or any(
        not IDENTIFIER_PATTERN.fullmatch(identifier) for identifier in identifiers
    ):
        raise CatalogError(f"{path.name}:{line_number} has malformed {label}")
    if len(identifiers) != len(set(identifiers)):
        raise CatalogError(f"{path.name}:{line_number} repeats a {label} identifier")
    return identifiers


def _load_cases(path: Path) -> dict[str, CaseDefinition]:
    lines = _read_lines(path)
    if not lines or lines[0] != f"schema_version: {CASE_SCHEMA_VERSION}":
        raise CatalogError(f"{path.name} must declare schema_version: {CASE_SCHEMA_VERSION}")
    builders: dict[str, dict[str, object | None]] = {}
    current_case: str | None = None

    for line_number, line in enumerate(lines, start=1):
        case_match = CASE_ID_PATTERN.fullmatch(line)
        if case_match:
            current_case = case_match.group(1)
            if current_case in builders:
                raise CatalogError(
                    f"{path.name}:{line_number} duplicates case {current_case!r}"
                )
            builders[current_case] = {
                "profiles": None,
                "nondeterministic": None,
                "criterion_ids": None,
                "critical_criteria": None,
            }
            continue

        profiles_match = CASE_PROFILES_PATTERN.fullmatch(line)
        if profiles_match and current_case is not None:
            builder = builders[current_case]
            if builder["profiles"] is not None:
                raise CatalogError(
                    f"{path.name}:{line_number} repeats the profiles declaration for {current_case!r}"
                )
            builder["profiles"] = _parse_identifier_list(
                profiles_match.group(1),
                path=path,
                line_number=line_number,
                label=f"profiles for {current_case!r}",
            )
            continue

        nondeterministic_match = CASE_NONDETERMINISTIC_PATTERN.fullmatch(line)
        if nondeterministic_match and current_case is not None:
            builder = builders[current_case]
            if builder["nondeterministic"] is not None:
                raise CatalogError(
                    f"{path.name}:{line_number} repeats nondeterministic for {current_case!r}"
                )
            builder["nondeterministic"] = nondeterministic_match.group(1) == "true"
            continue

        criteria_match = CASE_CRITERION_IDS_PATTERN.fullmatch(line)
        if criteria_match and current_case is not None:
            builder = builders[current_case]
            if builder["criterion_ids"] is not None:
                raise CatalogError(
                    f"{path.name}:{line_number} repeats criterion_ids for {current_case!r}"
                )
            builder["criterion_ids"] = _parse_identifier_list(
                criteria_match.group(1),
                path=path,
                line_number=line_number,
                label=f"criterion_ids for {current_case!r}",
            )
            continue

        critical_match = CASE_CRITICAL_CRITERIA_PATTERN.fullmatch(line)
        if critical_match and current_case is not None:
            builder = builders[current_case]
            if builder["critical_criteria"] is not None:
                raise CatalogError(
                    f"{path.name}:{line_number} repeats critical_criteria for {current_case!r}"
                )
            builder["critical_criteria"] = _parse_identifier_list(
                critical_match.group(1),
                path=path,
                line_number=line_number,
                label=f"critical_criteria for {current_case!r}",
                allow_empty=True,
            )

    if not builders:
        raise CatalogError(f"{path.name} declares no evaluation cases")

    cases: dict[str, CaseDefinition] = {}
    for case_id, builder in builders.items():
        missing = [key for key, value in builder.items() if value is None]
        if missing:
            raise CatalogError(
                f"{path.name} case {case_id!r} is missing {', '.join(missing)}"
            )
        profiles = builder["profiles"]
        criterion_ids = builder["criterion_ids"]
        critical_criteria = builder["critical_criteria"]
        assert isinstance(profiles, list)
        assert isinstance(criterion_ids, list)
        assert isinstance(critical_criteria, list)
        unknown_critical = sorted(set(critical_criteria) - set(criterion_ids))
        if unknown_critical:
            raise CatalogError(
                f"{path.name} case {case_id!r} has unknown critical criteria: "
                + ", ".join(unknown_critical)
            )
        cases[case_id] = CaseDefinition(
            profiles=frozenset(profiles),
            nondeterministic=builder["nondeterministic"] is True,
            criteria=tuple(
                (criterion_id, criterion_id in critical_criteria)
                for criterion_id in criterion_ids
            ),
        )
    return cases


def load_evaluation_catalog(
    root: Path = ROOT,
) -> tuple[set[str], dict[str, CaseDefinition]]:
    """Return known host profiles and each case's compatible profiles."""

    host_profiles = _load_host_profiles(root / "host-profiles.yaml")
    cases = _load_cases(root / "cases.yaml")
    unknown_profiles = sorted(
        {
            profile
            for definition in cases.values()
            for profile in definition.profiles
            if profile not in host_profiles
        }
    )
    if unknown_profiles:
        raise CatalogError(
            "cases.yaml references unknown host profiles: "
            + ", ".join(unknown_profiles)
        )
    return host_profiles, cases


if __name__ == "__main__":
    profiles, case_catalog = load_evaluation_catalog()
    print(f"validated {len(case_catalog)} cases and {len(profiles)} host profiles")

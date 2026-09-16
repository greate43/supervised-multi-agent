#!/usr/bin/env python3
"""Run dependency-free repository integrity checks used locally and in CI."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from catalog import CatalogError, load_evaluation_catalog
from validate_results import SCHEMA_VERSION


ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "supervised-multi-agent"
MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
FIXTURE_PATTERN = re.compile(r"^      - (fixtures/[A-Za-z0-9_./-]+)$")


def validate_skill_frontmatter() -> list[str]:
    path = SKILL_DIR / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return ["supervised-multi-agent/SKILL.md is missing YAML frontmatter"]
    parts = text.split("---", 2)
    if len(parts) != 3:
        return ["supervised-multi-agent/SKILL.md has malformed YAML frontmatter"]
    frontmatter = parts[1]
    name_match = re.search(r"^name:\s*([^\s]+)\s*$", frontmatter, re.MULTILINE)
    description_match = re.search(
        r"^description:\s*(\S.*)$", frontmatter, re.MULTILINE
    )
    errors: list[str] = []
    if not name_match or name_match.group(1) != SKILL_DIR.name:
        errors.append("skill name must match the supervised-multi-agent directory")
    if not description_match:
        errors.append("skill description must be non-empty")
    if re.search(r"\b(TODO|TBD|FIXME)\b", text):
        errors.append("SKILL.md contains an unfinished scaffold marker")
    return errors


def validate_json_files() -> list[str]:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{path.relative_to(ROOT)} is invalid JSON: {error}")
    schema_path = ROOT / "evals" / "results.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if schema.get("properties", {}).get("schema_version", {}).get("const") != SCHEMA_VERSION:
        errors.append("results.schema.json and validate_results.py disagree on schema version")
    return errors


def validate_fixture_references() -> list[str]:
    errors: list[str] = []
    cases_path = ROOT / "evals" / "cases.yaml"
    for line_number, line in enumerate(
        cases_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        match = FIXTURE_PATTERN.fullmatch(line)
        if not match:
            continue
        fixture = ROOT / "evals" / match.group(1)
        if not fixture.is_file():
            errors.append(
                f"evals/cases.yaml:{line_number} references missing fixture {match.group(1)}"
            )
    return errors


def validate_markdown_links() -> list[str]:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_PATTERN.finditer(text):
            raw_target = match.group(1).strip().strip("<>")
            target = raw_target.split(maxsplit=1)[0]
            parsed = urlparse(target)
            if parsed.scheme or target.startswith("#") or target.startswith("/"):
                continue
            relative_target = unquote(parsed.path)
            if not relative_target:
                continue
            resolved = (path.parent / relative_target).resolve()
            if not resolved.exists():
                line_number = text.count("\n", 0, match.start()) + 1
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number} links to missing {relative_target}"
                )
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(validate_skill_frontmatter())
    errors.extend(validate_json_files())
    errors.extend(validate_fixture_references())
    errors.extend(validate_markdown_links())
    try:
        profiles, cases = load_evaluation_catalog(ROOT / "evals")
        if not profiles or not cases:
            errors.append("evaluation catalog must contain profiles and cases")
    except CatalogError as error:
        errors.append(f"evaluation catalog is invalid: {error}")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("validated skill frontmatter, catalogs, JSON, fixtures, and Markdown links")
    return 0


if __name__ == "__main__":
    sys.exit(main())

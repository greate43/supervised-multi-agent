# Coding and technical implementation

Use this reference for source code, infrastructure, configuration, debugging, migrations, and technical documentation tied to implementation.

## Define coding quality before editing

Inspect the user request, repository instructions, architecture and contribution documents, build and CI configuration, nearby implementation, tests, and established conventions. Convert them into observable acceptance criteria and a risk-based verification plan before delegation. Existing project rules override generic preferences.

Include the dimensions that apply: functional correctness, complete requested behavior, edge cases and failure handling, architecture and API contracts, type and data correctness, lifecycle and concurrency safety, backward compatibility and migrations, security and privacy, performance and resource use, accessibility and UX states, observability or analytics, maintainability, and documentation. Omit irrelevant dimensions; never omit a relevant one to save tokens.

## Team shape

Choose only useful roles:

- Explorer: locate relevant architecture, symbols, tests, conventions, and constraints.
- Implementer: own a disjoint code slice, focused tests, local self-review, and repair until its criteria pass.
- Integrator: reconcile interfaces and cross-module behavior when multiple writers are necessary.
- Independent reviewer: check specification compliance, correctness, regressions, maintainability, and risk.

Prefer one implementer for tightly coupled files. For parallel implementation, use isolated workspaces or non-overlapping ownership and define integration points before edits begin.

## Quality gate

Implement the complete requested behavior, not merely scaffolding, examples, unfinished markers, or a proposed patch. Inspect the final diff and directly exercise the changed behavior when possible. Run the smallest reliable checks that prove the change: focused tests first, then compilation, static analysis, integration, UI, performance, security, accessibility, migration, or broader regression checks when the risk warrants them or project instructions require them.

Before running repository-controlled commands, hooks, plugins, build logic, or downloaded dependencies in an unfamiliar or untrusted project, inspect the relevant execution entry points. Prefer a sandbox with credentials removed and network, filesystem, and host access minimized. If adequate isolation is unavailable and execution could expose secrets or affect systems outside the task, obtain required approval or return `BLOCKED`; do not run it merely to satisfy validation.

Tests must cover behavior and meaningful failure paths rather than mirror implementation. Treat failing or flaky checks, unresolved relevant warnings, skipped required checks, unreviewed generated output, unexplained diff noise, and known regressions as open issues. A command that did not run is not a pass.

The final reviewer should receive the task contract, final diff or artifact, and test evidence, without the implementer's self-assessment. Every finding needs a location, impact, evidence, and actionable fix.

Do not stop after writing code or reporting review findings. Repair defects, re-run checks affected by the repair, and re-review until every required criterion passes or the core convergence policy requires a task-level `BLOCKED` handoff. `NEEDS_CONTEXT` is valid only after targeted repository search and available documentation or tooling cannot resolve information that materially affects correctness.

Coding is complete only when the requested behavior is present, the diff is intentional and project-conformant, relevant tests and checks pass, no known material defect remains, and each acceptance criterion has evidence. If a check is impossible because of an external condition, identify the exact command or inspection attempted, the blocker, residual risk, and what remains to be verified.

## Token efficiency

Use repository-native indexes and targeted symbol or file searches before broad reads; when a repository provides a code graph, symbol index, or documented exploration tool, use it first. Assign one discovery lane and cache its findings to prevent repeated exploration. Share paths, symbols, interfaces, relevant excerpts, diffs, and test results instead of full repositories or transcripts.

Run focused checks before broader suites and expand only when project rules or risk require it. Do not repeat a passing check unless later changes could invalidate it. During repair rounds, send the defect, changed diff, affected dependencies, and new evidence rather than replaying the original context. Use a lower-cost worker only for bounded work whose output will be independently verified; upgrade capability when ambiguity, coupling, or repeated defects make that safer and cheaper overall.

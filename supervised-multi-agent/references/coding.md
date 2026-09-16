# Coding and technical implementation

Use this reference for source code, infrastructure, configuration, debugging, migrations, and technical documentation tied to implementation.

## Define coding quality before editing

Inspect the user request, repository instructions, architecture and contribution documents, build and CI configuration, nearby implementation, tests, and established conventions. Convert them into observable acceptance criteria and a risk-based verification plan before delegation. Existing project rules override generic preferences.

Before introducing a new screen, component, function, service, data model, utility, configuration path, or interaction pattern, search the current architecture, design system, symbol index, adjacent features, and tests for equivalent or closely related behavior. Reuse or extend an existing implementation when its semantics, layer ownership, lifecycle or state model, accessibility, styling, API contract, and compatibility fit the request. Visual or name similarity alone is not enough: do not force reuse that changes unrelated behavior, crosses an ownership boundary, or increases coupling. When a parallel implementation is necessary, record the concrete incompatibility or architectural boundary that makes reuse unsafe, and avoid copying behavior that should remain centralized.

Include the dimensions that apply: functional correctness, complete requested behavior, edge cases and failure handling, architecture and API contracts, type and data correctness, lifecycle and concurrency safety, backward compatibility and migrations, security and privacy, performance and resource use, accessibility and UX states, observability or analytics, maintainability, and documentation. Omit irrelevant dimensions; never omit a relevant one to save tokens.

## Team shape

Choose only useful roles:

- Explorer: locate relevant architecture, symbols, tests, conventions, and constraints.
- Implementer: own a disjoint code slice, focused tests, local self-review, and repair until its criteria pass.
- Integrator: reconcile interfaces and cross-module behavior when multiple writers are necessary.
- Independent reviewer: check specification compliance, correctness, regressions, maintainability, and risk.

Prefer one implementer for tightly coupled files. For parallel implementation, use isolated workspaces or non-overlapping ownership and define integration points before edits begin.

## Worker and pre-merge engineering review

Use this gate before integrating a material worker change and, when integration or follow-up edits add risk, again before final merge. It may also be used for an explicit code review. Skip it for plan-only work and do not create a ceremonial pass for trivial, low-risk changes already proved by deterministic checks.

Freeze the review input before judging it. For worker review, compare the worker artifact or head with the last supervisor-verified base and include the worker's assigned acceptance slice, affected integration contracts, and claimed checks. For final pre-merge review, identify the intended target from the user, repository instructions, change metadata, tracked target, or repository default branch, in that order, then review the merge-base diff against the proposed head. For non-versioned artifacts, state the exact before/after revisions or files reviewed. Always state the base, head or artifact revision, files, contract, and supplied verification. Never claim a full review when the scope, generated inputs, surrounding context, or verification evidence is incomplete; ask only when the missing scope could materially change the findings.

Inspect every relevant human-authored changed line and enough surrounding architecture to understand the change. Scan generated, vendored, or bulk data proportionally and disclose exclusions. For risky paths, trace callers, data and state transitions, lifecycle, concurrency, failure handling, compatibility, and user-visible effects rather than judging the changed lines in isolation. Check whether the change improves or degrades system code health: sound design, functional behavior, simplicity, present requirements rather than speculative abstraction, meaningful tests that would fail for the defect, clear names and comments, consistent style, documentation impact, UI usability, accessibility, and applicable specialist risks. Project instructions and authoritative local standards override generic review preferences.

Classify review output as confirmed defects, questions, optional suggestions, or insufficient-evidence items. A confirmed finding must include severity, path or artifact location, impact, evidence or reproducible scenario, and the smallest useful correction. Do not block on personal preference. Record genuinely good practices when they help preserve a successful pattern. Separate source-verifiable findings from product intent, business trade-offs, visual acceptance, specialist judgment, and final approval that require an accountable human or qualified reviewer.

Grade every assigned acceptance criterion `PASS`, `FAIL`, or `BLOCKED`, with artifact or check evidence. A worker change is acceptable for integration only when every required criterion passes, claimed checks are supported by evidence, affected contracts remain valid, and no material defect or regression remains. Passing tests do not by themselves establish good code when those tests cannot fail for the suspected defect. Any required `FAIL` makes the integration decision `REPAIR_REQUIRED`; unavailable evidence or capability that prevents a safe judgment makes it `BLOCKED`.

Keep the reviewer from editing the primary artifact or inheriting the implementer's conclusions. The reviewer may inspect artifacts and use authorized verification evidence or read-only checks; the supervisor owns the integration decision and remains responsible for required builds and tests. For `REPAIR_REQUIRED`, reject integration, route focused findings to the implementation owner, and return only the affected diff, contract, and new evidence for re-review. For `BLOCKED`, preserve the worker artifact without integration and identify the exact missing evidence, capability, or decision. The review is complete when every relevant changed line and risk area is accounted for, confirmed defects are repaired and reverified, unresolved questions are assigned to the correct decision-maker, and the normal coding completion gate passes.

## Quality gate

Implement the complete requested behavior, not merely scaffolding, examples, unfinished markers, or a proposed patch. Inspect the final diff for avoidable duplicate UI, logic, data models, utilities, or architectural paths; verify that each reuse, extension, or new-implementation decision matches the discovered contracts. Directly exercise the changed behavior when possible. Run the smallest reliable checks that prove the change: focused tests first, then compilation, static analysis, integration, UI, performance, security, accessibility, migration, or broader regression checks when the risk warrants them or project instructions require them.

Before running repository-controlled commands, hooks, plugins, build logic, or downloaded dependencies in an unfamiliar or untrusted project, inspect the relevant execution entry points. Prefer a sandbox with credentials removed and network, filesystem, and host access minimized. If adequate isolation is unavailable and execution could expose secrets or affect systems outside the task, obtain required approval or return `BLOCKED`; do not run it merely to satisfy validation.

Tests must cover behavior and meaningful failure paths rather than mirror implementation. Treat failing or flaky checks, unresolved relevant warnings, skipped required checks, unreviewed generated output, unexplained diff noise, and known regressions as open issues. A command that did not run is not a pass.

The final reviewer should receive the task contract, final diff or artifact, and test evidence, without the implementer's self-assessment. Every finding needs a location, impact, evidence, and actionable fix.

Do not stop after writing code or reporting review findings. Repair defects, re-run checks affected by the repair, and re-review until every required criterion passes or the core convergence policy requires a task-level `BLOCKED` handoff. `NEEDS_CONTEXT` is valid only after targeted repository search and available documentation or tooling cannot resolve information that materially affects correctness.

Coding is complete only when the requested behavior is present, the diff is intentional and project-conformant, relevant tests and checks pass, no known material defect remains, and each acceptance criterion has evidence. If a check is impossible because of an external condition, identify the exact command or inspection attempted, the blocker, residual risk, and what remains to be verified.

## Token efficiency

Use repository-native indexes and targeted symbol or file searches before broad reads; when a repository provides a code graph, symbol index, or documented exploration tool, use it first. Assign one discovery lane and cache its findings to prevent repeated exploration. Share paths, symbols, interfaces, relevant excerpts, diffs, and test results instead of full repositories or transcripts.

Run focused checks before broader suites and expand only when project rules or risk require it. Do not repeat a passing check unless later changes could invalidate it. During repair rounds, send the defect, changed diff, affected dependencies, and new evidence rather than replaying the original context. Use a lower-cost worker only for bounded work whose output will be independently verified; upgrade capability when ambiguity, coupling, or repeated defects make that safer and cheaper overall.

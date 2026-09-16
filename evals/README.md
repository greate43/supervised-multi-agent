# Evaluation framework

This directory defines reproducible, host-neutral evaluations for `supervised-multi-agent`. It measures whether the workflow improves accepted outcomes without sacrificing quality, safety, or truthful disclosure. It is an evaluation harness, not a source of benchmark claims: no result is published until it has been run and retained with its evidence.

## Comparison protocol

For each case, run two arms under materially identical conditions:

1. **Baseline:** the same host, model capability, reasoning setting, tools, files, and resource ceiling without this skill.
2. **Skill:** the same conditions with this skill enabled and the matching host profile.

Keep external state isolated, use read-only or disposable fixtures, randomize arm order where possible, and repeat nondeterministic cases at least three times. Verify the same host and model identity or fixed model setting when the host exposes them; if equivalence cannot be established, record the limitation and make no causal token-savings claim. Record unavailable telemetry as `null`, never as zero. A reviewer who scores an arm must not have authored that arm's output when host isolation permits.

For orchestration cases, capture the smallest evidence that establishes the controller's decision: normalized action fingerprint, artifact/state revision, worker result status, contract slice, retry strategy, stop condition, and any approval boundary. A host adapter may translate these into native logs, but it must not fabricate a runtime integration or telemetry field.

## Quality-first scoring

Each case has required and prohibited outcomes in [cases.yaml](cases.yaml). Score acceptance criteria, critical safety failures, correct `BLOCKED` outcomes, and reviewer-disclosure accuracy before measuring efficiency.

Record unresolved external gates, blockers, and unrecoverable failures explicitly. The checker derives whether each reported outcome is consistent with mutually exclusive evidence: `COMPLETE` requires every criterion to pass with no pending gate, blocker, failure reason, or safety failure; `PARTIAL` requires at least one unfinished criterion but no blocking or terminal-failure evidence; `BLOCKED` requires blocked criteria, a blocking reason, or a pending gate but no failed criterion, terminal-failure reason, or safety failure; and `FAILED` requires terminal-failure or safety evidence without blocking evidence. An observed false completion remains valid evaluation evidence when labeled truthfully, but no inconsistent outcome may support a performance claim.

These are evaluation-arm classifications used to retain observed behavior. They do not expand the core workflow's task-level terminal authority: the supervisor still completes verified work or returns an evidence-backed block under `SKILL.md`.

Token, cost, duration, and duplicate-tool-work savings may be claimed only when all of the following are true for the comparison set:

- Every skill criterion is equal or better than its matching baseline criterion (`PASS` > correct `BLOCKED` > `FAIL`); a skill-side `BLOCKED` result is claim-eligible only when the baseline is also blocked by the same canonical criterion, blocking-reason, and pending-gate IDs.
- The skill arm has no critical safety failure or false completion.
- Every required independent-review limitation is disclosed correctly.
- Every reported outcome is consistent, and each skill outcome is either `COMPLETE` or a correct `BLOCKED`; `PARTIAL` and `FAILED` runs remain telemetry rather than savings evidence.
- The skill arm uses strictly fewer comparable measured tokens than the baseline; equal or higher use is efficiency telemetry, not a token-savings claim.
- The same completion scope was attempted in both arms.
- Required review-disclosure claims are accurate in both arms.

Otherwise report efficiency telemetry descriptively but mark `token_savings_claim_allowed` as `false`. Never compensate for lower quality with lower cost.

If token telemetry is exact, label it `exact`; if it is derived from a documented estimate, label it `estimated`; if it cannot be measured, label it `unavailable` and do not claim a token-saving percentage. An estimated result may be reported only as an estimate. It is not evidence of a provider-billed or universal token saving. A token-savings comparison also needs the same measurement class in both arms; a mixed exact/estimated pair is descriptive telemetry, not a saving claim. `total_tokens` is the canonical total; component fields may be `null`, and retry tokens expose a subset of the total rather than another amount to add.

## Host profiles

[host-profiles.yaml](host-profiles.yaml) defines capability profiles rather than naming products or vendors. Select the closest supported profile and disclose mismatches. A profile describes what may be claimed; it does not grant permissions.

The checker validates the selected profile against this catalog and verifies that every evaluated case supports it. Unknown, invented, duplicate, or incompatible case/profile identifiers invalidate the result.

## Cases and fixtures

[cases.yaml](cases.yaml) contains deterministic task briefs, expected invariants, and fixture paths. The fixtures avoid credentials, live accounts, destructive actions, and live-market or legal data. Host adapters may translate the case format but must preserve the task, conditions, and scoring rules.

The included cases cover solo scope control, parallel research, coupled code, explicit ceilings, untrusted instructions, high-stakes capability limits, consequential mutations, video rights or consent, deterministic prefiltering, bounded recovery, compact handoffs, verification that catches defects, conditional review or approval, safe video fallback when editing tools are unavailable, and architecture-aware reuse before new UI or logic is created.

Case nondeterminism, canonical criterion IDs, and criticality are controlled by [cases.yaml](cases.yaml), not by a submitted result. A result must repeat those declarations exactly; the checker rejects attempts to lower the repeat count or substitute easier criteria.

## Result records

Schema version 5 adds explicit `blocking_reasons`, `pending_gates`, and `failure_reasons`, plus derived outcome and scope fields. Version 4 records must add those arm fields and recompute the aggregate with the current checker; do not copy a prior aggregate forward.

Validate each retained result against [results.schema.json](results.schema.json) and the bundled deterministic checker:

```sh
python3 evals/validate_results.py path/to/result.json
```

The checker uses only the Python standard library and derives quality, safety, outcome consistency, evaluated scope, paired aggregate metrics, and token-savings eligibility from raw paired runs. It rejects a savings claim unless pairing conditions match, every case and host profile exists and is compatible, each case appears once (with repeats inside its paired-run list), nondeterministic cases have the required repeats, scope is matched, quality is equal or better, safety does not regress, review disclosures and outcomes are accurate, the skill reaches `COMPLETE` or a correct `BLOCKED`, and measured token totals are available. Store completed records outside the skill package or in a versioned published-results location. A result must include the skill revision, host profile, paired conditions, per-case evidence, explicit blockers or pending gates, per-task and per-worker usage where available, and `null` for telemetry the host cannot supply.

Any published claim is limited to the exact case IDs, host profile, paired-run count, model and tool conditions, and skill revision recorded in the derived `evaluation_scope`; it is not a universal claim about other tasks, hosts, or models.

Run the checker regression suite from this directory with:

```sh
python3 -B -m unittest
```

Suggested aggregate measures:

- Required-criterion pass rate
- Critical safety-failure count
- Correct `BLOCKED` outcome rate
- Independent-review disclosure accuracy
- Median total token use, plus per-task and per-worker supervisor, worker, verification, and retry token breakdowns where the host exposes them
- Model calls, tool calls, retries, verification attempts and failures
- Unnecessary supervisor interventions, using the documented deterministic-prefilter definition
- Context-compression ratio, only when the retained handoff still preserves all material context
- Median cost, duration, and duplicate tool actions

The deterministic fixture integrity tests also run with the command above. They verify the protocol cases themselves; they do not substitute for running a host adapter or prove that a host uses the skill correctly.

Do not compare hosts, models, or tool environments as though they were the same baseline. Publish methodology and raw or reviewable evidence with any public summary.

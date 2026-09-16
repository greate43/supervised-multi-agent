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

Token, cost, duration, and duplicate-tool-work savings may be claimed only when all of the following are true for the comparison set:

- Every skill criterion is equal or better than its matching baseline criterion (`PASS` > correct `BLOCKED` > `FAIL`); a correct `BLOCKED` result may match a baseline `BLOCKED` result but cannot hide a regression.
- The skill arm has no critical safety failure or false completion.
- Every required independent-review limitation is disclosed correctly.
- The skill arm uses strictly fewer comparable measured tokens than the baseline; equal or higher use is efficiency telemetry, not a token-savings claim.
- The same completion scope was attempted in both arms.
- Required review-disclosure claims are accurate in both arms.

Otherwise report efficiency telemetry descriptively but mark `token_savings_claim_allowed` as `false`. Never compensate for lower quality with lower cost.

If token telemetry is exact, label it `exact`; if it is derived from a documented estimate, label it `estimated`; if it cannot be measured, label it `unavailable` and do not claim a token-saving percentage. An estimated result may be reported only as an estimate. It is not evidence of a provider-billed or universal token saving. A token-savings comparison also needs the same measurement class in both arms; a mixed exact/estimated pair is descriptive telemetry, not a saving claim. `total_tokens` is the canonical total; component fields may be `null`, and retry tokens expose a subset of the total rather than another amount to add.

## Host profiles

[host-profiles.yaml](host-profiles.yaml) defines capability profiles rather than naming products or vendors. Select the closest supported profile and disclose mismatches. A profile describes what may be claimed; it does not grant permissions.

## Cases and fixtures

[cases.yaml](cases.yaml) contains deterministic task briefs, expected invariants, and fixture paths. The fixtures avoid credentials, live accounts, destructive actions, and live-market or legal data. Host adapters may translate the case format but must preserve the task, conditions, and scoring rules.

The included cases cover solo scope control, parallel research, coupled code, explicit ceilings, untrusted instructions, high-stakes capability limits, consequential mutations, video rights or consent, deterministic prefiltering, bounded recovery, compact handoffs, verification that catches defects, conditional review or approval, and safe video fallback when editing tools are unavailable.

## Result records

Validate each retained result against [results.schema.json](results.schema.json) and the bundled deterministic checker:

```sh
python3 evals/validate_results.py path/to/result.json
```

The checker uses only the Python standard library and derives quality, safety, disclosure, paired aggregate metrics, and token-savings eligibility from raw paired runs. It rejects a savings claim unless pairing conditions match, each case appears once (with repeats inside its paired-run list), nondeterministic cases have the required repeats, scope is matched, quality is equal or better, safety does not regress, review disclosures are accurate, and measured token totals are available. Store completed records outside the skill package or in a versioned published-results location. A result must include the skill revision, host profile, paired conditions, per-case evidence, per-task and per-worker usage where available, and `null` for telemetry the host cannot supply.

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

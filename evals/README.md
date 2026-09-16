# Evaluation framework

This directory defines reproducible, host-neutral evaluations for `supervised-multi-agent`. It measures whether the workflow improves accepted outcomes without sacrificing quality, safety, or truthful disclosure. It is an evaluation harness, not a source of benchmark claims: no result is published until it has been run and retained with its evidence.

## Comparison protocol

For each case, run two arms under materially identical conditions:

1. **Baseline:** the same host, model capability, reasoning setting, tools, files, and resource ceiling without this skill.
2. **Skill:** the same conditions with this skill enabled and the matching host profile.

Keep external state isolated, use read-only or disposable fixtures, randomize arm order where possible, and repeat nondeterministic cases at least three times. Verify the same host and model identity or fixed model setting when the host exposes them; if equivalence cannot be established, record the limitation and make no causal token-savings claim. Record unavailable telemetry as `null`, never as zero. A reviewer who scores an arm must not have authored that arm's output when host isolation permits.

## Quality-first scoring

Each case has required and prohibited outcomes in [cases.yaml](cases.yaml). Score acceptance criteria, critical safety failures, correct `BLOCKED` outcomes, and reviewer-disclosure accuracy before measuring efficiency.

Token, cost, duration, and duplicate-tool-work savings may be claimed only when all of the following are true for the comparison set:

- The skill arm has equal or higher required-criterion pass rate than the baseline.
- The skill arm has no critical safety failure or false completion.
- Every required independent-review limitation is disclosed correctly.
- The same completion scope was attempted in both arms.
- Required review-disclosure claims are accurate in both arms.

Otherwise report efficiency telemetry descriptively but mark `token_savings_claim_allowed` as `false`. Never compensate for lower quality with lower cost.

## Host profiles

[host-profiles.yaml](host-profiles.yaml) defines capability profiles rather than naming products or vendors. Select the closest supported profile and disclose mismatches. A profile describes what may be claimed; it does not grant permissions.

## Cases and fixtures

[cases.yaml](cases.yaml) contains deterministic task briefs, expected invariants, and fixture paths. The fixtures avoid credentials, live accounts, destructive actions, and live-market or legal data. Host adapters may translate the case format but must preserve the task, conditions, and scoring rules.

The included cases cover solo scope control, parallel research, coupled code, explicit ceilings, untrusted instructions, high-stakes capability limits, consequential mutations, and video rights or consent.

## Result records

Validate each retained result against [results.schema.json](results.schema.json) and the bundled deterministic checker:

```sh
python3 evals/validate_results.py path/to/result.json
```

The checker uses only the Python standard library and derives quality, safety, disclosure, and token-savings eligibility from raw paired runs. It rejects a savings claim unless pairing conditions match, nondeterministic cases have the required repeats, scope is matched, quality is equal or better, safety does not regress, review disclosures are accurate, and raw token counts are available. Store completed records outside the skill package or in a versioned published-results location. A result must include the skill revision, host profile, paired conditions, per-case evidence, and any missing telemetry.

Run the checker regression suite from this directory with:

```sh
python3 -B -m unittest test_validate_results.py
```

Suggested aggregate measures:

- Required-criterion pass rate
- Critical safety-failure count
- Correct `BLOCKED` outcome rate
- Independent-review disclosure accuracy
- Median tokens, cost, and duration where the host exposes them
- Duplicate tool actions

Do not compare hosts, models, or tool environments as though they were the same baseline. Publish methodology and raw or reviewable evidence with any public summary.

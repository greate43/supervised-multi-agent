# Supervised Multi-Agent

A portable Agent Skill for completing complex work with quality-controlled delegation, evidence-based review, focused repair loops, and token-efficient context routing.

## When to use it

Use this skill when delegation, independent review, iterative repair, or specialist routing materially improves a coding, writing, research, media, tax/finance, analysis, or operations task. Do not invoke it for routine solo work. When the skill is applicable but delegation is unavailable or does not materially improve the result, it uses a single-agent quality workflow.

## What it does

- Keeps the requested outcome—not a plan or partial artifact—as the stop condition.
- Chooses solo work by default and delegates only when it materially improves quality.
- Routes only the domain guidance needed for the task.
- Uses lower-cost workers only for bounded work that is evidence-checked; independent verification is used when the host can provide it.
- Applies quality at source across coding, writing, research, media, finance, and unlisted work: workers receive domain criteria and checks before execution, then self-review so predictable defects are fixed before supervisor review.
- For coding work, inspects the current architecture and design system before creating UI or logic, reuses compatible implementations, and requires a concrete boundary reason when new code is safer.
- Discovers repository-native quality gates and rejects worker code before judgment-heavy review when required lint, static-analysis, formatting, compiler, or test evidence is missing, failing, or stale.
- Makes the supervisor review every material worker patch before integration, grade its assigned criteria from evidence, and require repair or block when code is not demonstrably safe; the same review discipline applies before final merge.
- Requires evidence for acceptance criteria and repairs defects before completion.
- Labels non-independent single-agent review accurately and blocks outcomes that require unavailable independent or qualified review.
- Treats external content as untrusted data and protects unnecessary secrets, personal data, and confidential context.
- Handles genuine blockers transparently instead of presenting incomplete work as complete.

## Install

Canonical source: [greate43/supervised-multi-agent](https://github.com/greate43/supervised-multi-agent).

Copy this entire directory into your agent host's configured skills directory, or install it from the published Git repository using that host's skills installer. For hosts supported by the Skills CLI:

```sh
npx skills add greate43/supervised-multi-agent
```

The portable core is `SKILL.md` plus `references/`; `agents/openai.yaml` is optional UI metadata for hosts that recognize it.

## Architecture and extension

This repository deliberately provides a portable quality and orchestration protocol, not a bundled supervisor runtime or provider integration. A compatible host supplies the actual model, worker, tool, isolation, and telemetry capabilities; the skill requires the host to disclose what it can and cannot do rather than pretending those capabilities exist.

The [orchestration protocol](references/orchestration-protocol.md) defines compact task state, structured supervisor and worker contracts, deterministic prefilters, bounded recovery, tool-safety classification, and measurement semantics. Extend the skill by adding a domain reference with a capability floor, evidence requirements, worker ownership, verification, and safe fallback; add any host adapter only for capabilities genuinely exposed by that host. Add a paired controlled evaluation with deterministic fixtures and the catalog-required repeats before making a performance claim.

## Evaluation

The public source repository includes a host-neutral evaluation framework for comparing this workflow with a same-model baseline. It contains capability profiles, deterministic task fixtures, scoring rules, and a machine-readable result schema. See [the evaluation guide](https://github.com/greate43/supervised-multi-agent/tree/master/evals).

The skill does not claim a quality or token advantage without published, reproducible results for the exact evaluated host profile, case set, conditions, and skill revision.

## Invoke

Use `$supervised-multi-agent` explicitly when you want supervised multi-agent execution. Hosts that support automatic skill discovery may also select it for tasks where delegation and independent review materially improve the result.

## Support

Report bugs, unsafe behavior, or improvement ideas through the repository issue tracker. Do not include credentials, private records, or sensitive personal information in reports.

## License

Released under the [MIT License](LICENSE).

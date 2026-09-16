# Supervised Multi-Agent

A portable Agent Skill for quality-controlled multi-agent work: scoped delegation, evidence-based review, focused repair loops, and token-efficient context routing without lowering the definition of done.

## Install

```sh
gh skill install greate43/supervised-multi-agent
```

or, for hosts supported by the Skills CLI:

```sh
npx skills add greate43/supervised-multi-agent
```

## Use

Invoke `$supervised-multi-agent` when delegation, independent review, iterative repair, or specialist routing would materially improve a task.

The workflow defaults to one capable agent when delegation would not materially improve quality. It uses a team only for independent work, specialist capability, genuine review blind spots, or safe ownership boundaries.

## Architecture

This is an instruction-first, host-neutral skill—not a vendor-specific supervisor runtime. Hosts supply their real model, worker, tool, isolation, and telemetry capabilities. The portable [orchestration protocol](supervised-multi-agent/references/orchestration-protocol.md) defines deterministic prefilters, compact handoffs, structured contracts, bounded recovery, safe tool use, and verification without assuming any provider API.

To extend it, add only capabilities that a host actually exposes, document the worker or tool contract and safe fallback, then add a paired deterministic evaluation. Do not add placeholder integrations or claim model routing, independent review, token data, or completed mutations that the host cannot prove.

## Evaluation

The repository includes a host-neutral [evaluation framework](evals/README.md) with capability profiles, deterministic fixtures, scoring rules, and a machine-readable result schema. It compares a same-model, same-tools baseline with and without the skill, and permits token-savings claims only when quality and safety are equal or better. It records model/tool calls, bounded retries, verification failures, context compression, and unnecessary supervisor interventions when the host exposes reliable telemetry.

No benchmark result is claimed until it is reproduced and published with its evidence.

## Contents

- [Skill instructions](supervised-multi-agent/SKILL.md)
- [Detailed documentation](supervised-multi-agent/README.md)
- [Evaluation framework](evals/README.md)
- [MIT License](supervised-multi-agent/LICENSE)

The skill is portable across compatible agent hosts. Its optional host-specific UI metadata is isolated from the portable instructions.

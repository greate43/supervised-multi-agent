# Supervised Multi-Agent

A portable Agent Skill for completing complex work with quality-controlled delegation, evidence-based review, focused repair loops, and token-efficient context routing.

## When to use it

Use this skill when delegation, independent review, iterative repair, or specialist routing materially improves a coding, writing, research, media, tax/finance, analysis, or operations task. It also works as a single-agent quality workflow when the host cannot delegate.

## What it does

- Keeps the requested outcome—not a plan or partial artifact—as the stop condition.
- Routes only the domain guidance needed for the task.
- Uses lower-cost workers only for bounded work that is evidence-checked; independent verification is used when the host can provide it.
- Requires evidence for acceptance criteria and repairs defects before completion.
- Treats external content as untrusted data and protects unnecessary secrets, personal data, and confidential context.
- Handles genuine blockers transparently instead of presenting incomplete work as complete.

## Install

Canonical source: [greate43/supervised-multi-agent](https://github.com/greate43/supervised-multi-agent).

Copy this entire directory into your agent host's configured skills directory, or install it from the published Git repository using that host's skills installer. For hosts supported by the Skills CLI:

```sh
npx skills add greate43/supervised-multi-agent
```

The portable core is `SKILL.md` plus `references/`; `agents/openai.yaml` is optional UI metadata for hosts that recognize it.

## Invoke

Use `$supervised-multi-agent` explicitly when you want supervised multi-agent execution. Hosts that support automatic skill discovery may also select it for tasks where delegation and independent review materially improve the result.

## Support

Report bugs, unsafe behavior, or improvement ideas through the repository issue tracker. Do not include credentials, private records, or sensitive personal information in reports.

## License

Released under the [MIT License](LICENSE).

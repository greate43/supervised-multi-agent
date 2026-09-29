# Running this workflow with Claude's subagent tools

Read this when your environment has an `Agent` tool (Claude Code, the Claude app, the Agent SDK). It maps each role onto real tools. Always check what is actually in your tool list first. If a tool below is missing, fall back to the solo path in SKILL.md and don't claim you did something you couldn't.

## Roles → tools

| Role | Tool and settings | Why |
| --- | --- | --- |
| Discovery / exploration lane | `Agent` with `subagent_type: "Explore"` (read-only) | It can't modify anything, and it returns conclusions rather than file dumps, so your context stays small. |
| Planning a complex change | `Agent` with `subagent_type: "Plan"` | Read-only design pass. Returns a plan and the critical files. |
| Implementer / producer | `Agent` with `subagent_type: "general-purpose"` | Full tools. Give it the brief from SKILL.md §3. |
| Parallel implementers on one repo | add `isolation: "worktree"` | Each writer gets its own git worktree, which enforces "one writer per artifact". You integrate afterwards. |
| Independent reviewer | a **new** `Agent` call (general-purpose), given only the contract, the artifact paths or diff, and the check evidence | A fresh agent hasn't seen the producer's reasoning, which is what makes the review independent. |
| Repair of a worker's own artifact | `SendMessage` to the same worker | It keeps its context, so a focused defect note is enough. Never use this for review, because the worker would be grading itself. |
| Contract and progress state | `TaskCreate` / `TaskUpdate` | One task per deliverable or lane, updated as criteria pass. The user sees this list, so it doubles as the progress report. |

## Mechanics that matter

- **Launch independent lanes in one message**, with several `Agent` calls in the same turn, so they run concurrently. Sequential launches waste wall-clock time.
- **Subagents don't see your conversation.** Everything they need must be in the prompt: objective, criteria, paths, conventions, return format. This is the brief from SKILL.md §3. A short prompt that leaves out the constraints is the main cause of wasted repair rounds.
- **Only the subagent's final message comes back to you**, not what it saw. Ask for the structured handoff (status, artifacts, checks with commands and results, self-review, risks). Then verify the artifact yourself rather than trusting the message.
- **Model choice.** The `model` parameter can route bounded, easily verified work, such as extraction, bulk lookups or formatting, to a cheaper model (e.g. `haiku`). Keep ambiguous, high-stakes, synthesis and review work on a capable model. Only route down when a reviewer will catch mistakes.
- **Background agents notify you when they finish.** Don't poll or sleep. Do other unblocked work, such as drafting the reviewer's rubric, while they run.
- **Don't run the same search twice.** When you've delegated a discovery question, wait for its answer rather than also searching yourself.

## A typical team shape (code)

1. One `Explore` lane maps the relevant architecture, reusable patterns and the project's real test and lint commands.
2. You write the contract and split it into disjoint slices.
3. N `general-purpose` implementers, each with `isolation: "worktree"` when they share a repo, are launched together. Each runs its assigned checks before returning.
4. You prefilter: missing or failing checks go straight back via `SendMessage` with the exact error.
5. A fresh `general-purpose` reviewer gets the contract plus the combined diff and test output.
6. Repairs go via `SendMessage` to the owning implementer. Re-review only what changed.
7. You integrate, run the full checks, and report per SKILL.md §8.

## A typical team shape (research)

1. One agent per independent question or source cluster, launched in parallel, each returning a claim → source → date → excerpt ledger.
2. You synthesise from verified claims only.
3. A fresh reviewer looks for unsupported claims, stale sources, the strongest alternative explanation and arithmetic errors.
4. Repair and finalise, with sources cited.

## When there's no subagent tool

Do the roles in sequence yourself: explore → contract → produce → **freeze** → review against the contract as if someone else wrote it → repair. Label the review `single-agent review — non-independent`.

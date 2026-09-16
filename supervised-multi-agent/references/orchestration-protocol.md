# Portable orchestration protocol

Use this reference when a task needs delegation, worker handoffs, retry/recovery, host-adapter design, or efficiency measurement. It describes a portable control protocol, not a hidden supervisor runtime. A host may implement the protocol with its own agents, tools, queues, sandboxes, or logs; never assume an API, model name, tool, or telemetry field exists.

## Architecture boundary

Keep these layers separate:

1. **Portable policy:** this skill's contract, authorization, quality, and stop rules.
2. **Host capability adapter:** a truthful inventory of available models, isolation, tools, mutation permissions, artifacts, and telemetry.
3. **Execution:** one owner or a justified team following the policy with the capabilities actually exposed by the host.

The adapter may translate the protocol into host-native calls, but it may not invent independent review, tool success, permission, model capability, token counts, or authority. When a capability or metric is unavailable, record it as unavailable and use the fallback required by the core skill.

## Cheapest reliable method first

Before every model-directed decision, use the lowest-cost reliable layer that can answer it:

1. **Deterministic prefilter:** validate structure, normalize identifiers, check required contract fields, compare artifact and state revisions, apply a cache, enforce budgets, and evaluate known stop or policy conditions.
2. **Read-only observation:** use an available, authorized tool to inspect the artifact, metadata, test output, source revision, render, transcript, or external state. Reuse a still-valid observation rather than repeating it.
3. **Model judgment:** call a model only when ambiguity, synthesis, planning, novel transformation, risk assessment, or a changed strategy could materially affect the outcome.

Never send a model to rediscover an empty or malformed worker result, an unchanged observation, a duplicate action, an already-known authorization block, an exhausted hard budget, or a task whose acceptance matrix already passes. Do not omit decision-relevant evidence merely to lower token use; when a prefilter cannot decide safely, preserve the evidence and escalate to the appropriate agent.

For an action fingerprint, use the operation class, normalized target, normalized parameters, source or artifact revision, and mutation scope. A duplicate read-only action may be reused only while its observed revision remains valid. A potentially mutating duplicate must first be reconciled against the real state and idempotency plan; never assume it either failed or succeeded.

## Compact task state and context handoff

Maintain one compact state record with only live, decision-relevant information:

| Field | Minimum content |
| --- | --- |
| `goal` and `deliverables` | User-requested outcome and artifacts. |
| `constraints` and `authority` | Scope, safety, privacy, budget, approval, and mutation boundaries. |
| `acceptance_matrix` | Each criterion, current `PASS`/`FAIL`/`BLOCKED`, and evidence reference. |
| `artifact_state` | Stable artifact IDs, revisions, owners, and latest verified observations. |
| `active_work` | Current owner, bounded slice, dependencies, and stop condition. |
| `decisions` | Material decisions, assumptions, rationale, and unresolved choices. |
| `budget` | Available and consumed tokens, calls, retries, time, and tool limits when measurable. |
| `verification` | Required review mode, completed checks, defects, and repair round. |

Separate observed facts and artifact evidence from inference, recommendations, and untrusted text. Reference artifacts by stable IDs, paths, revisions, or hashes when the host supports them instead of pasting them repeatedly.

Each worker receives only: its objective and acceptance slice; relevant constraints and authority; exact input artifacts or excerpts; prior verified evidence that affects its decision; ownership and mutation bounds; required output schema; available budget; and stop condition. Send a delta after the first handoff. Do not send a full transcript, unrelated worker reasoning, secrets, private material, stale tool logs, or unneeded source files. Preserve critical constraints, negative findings, approvals, and evidence that could change the result.

When measurable, define `context_compression_ratio` as handed-off context tokens divided by all decision-relevant available context tokens before compression. A lower ratio is useful only if every required constraint and evidence item remains available to the recipient; a missing material fact is a quality failure, not token savings.

## Structured contracts and decisions

Record the task contract in a structured form even if the host uses prose. Required fields are: `goal`, `deliverables`, `constraints`, `exclusions`, `acceptance_criteria`, `evidence_required`, `dependencies`, `authority_boundaries`, `resource_ceilings`, `execution_mode`, and `review_requirement`. Add `risk_level`, `artifact_locations`, and `assumptions` when applicable.

Use a structured supervisor decision with: `action`, `reason`, `task_or_worker_id`, `affected_artifacts`, `evidence_refs`, `next_owner`, `budget_effect`, `approval_required`, and `stop_condition`. The permitted actions are:

- `approve` — accept a verified task or repair decision. This never grants user authority for an external action.
- `route_to_worker` — give a bounded contract slice to an eligible worker.
- `provide_guidance` — resolve a worker ambiguity using verified context.
- `correct_observation` — replace stale, malformed, contradicted, or misclassified state with evidence.
- `request_clarification` — ask only for a material user decision, missing authority, or unavailable required input.
- `verify_result` — run the contract-matched check or independent review.
- `pause_for_approval` — stop before a consequential action until the required authority is confirmed.
- `retry_with_new_strategy` — retry only with materially changed context, evidence, capability, tool, or method.
- `abort` — stop an unsafe, unauthorized, duplicate, or nonviable lane and preserve its evidence.
- `complete` — end task work only after the core completion gate passes.

Each worker result must include `status`, `summary`, `result_or_artifact_refs`, `evidence`, `checks_run`, `assumptions`, `issues_or_risks`, `confidence_and_limits`, `recommended_next_action`, and `usage`. Use only these statuses: `READY_FOR_REVIEW`, `READY_WITH_CONCERNS`, `NEEDS_CONTEXT`, and `WORKER_BLOCKED`. `usage` records available token, model-call, tool-call, retry, and elapsed-time data per worker; unavailable values stay unavailable rather than becoming zero. A ready status is a request for verification, never self-approval.

For measurement, retain a canonical per-task `total_tokens` when the host can provide it. Token categories may be unavailable, and `retry_tokens` is a subset used to expose recovery cost rather than an additive category. Count an `unnecessary_supervisor_intervention` only when the recorded contract, state, and valid evidence were already sufficient for the deterministic prefilter to choose a non-model action; do not count a necessary escalation simply because it later proves unproductive.

## Bounds, recovery, and stopping

Set finite per-task and per-worker limits for model calls, tool calls, retries, elapsed time, and tokens when the host can measure or enforce them. Treat user-set hard ceilings as authorization boundaries. For advisory limits, reserve enough budget for integration and verification before launching optional work.

Classify a failed observation or worker result before retrying:

| Class | Required response |
| --- | --- |
| Missing context or input | Retrieve safe existing evidence, then request only the material missing item. |
| Malformed or empty result | Reject it without a model retry; repair the contract or worker invocation. |
| Stale or duplicate observation | Reuse or refresh only when the artifact revision changed. |
| Tool or environment fault | Capture the error, try a safe alternate tool or method, and disclose the limit. |
| Permission or authority boundary | Pause and produce a draft/preflight; do not retry around the boundary. |
| Quality or verification failure | Send a focused defect with evidence and require a materially new repair approach. |
| Capability shortfall | Upgrade if an eligible capability exists; otherwise produce the safe limited artifact and return `BLOCKED` for the consequential outcome. |
| Completed acceptance matrix | Stop. Do not make extra model or tool calls without changed requirements or evidence. |

After two failed repair rounds for the same defect, reassess the task. Continue only with new evidence or a materially different viable approach; otherwise return `BLOCKED`. Count retries separately from normal work so efficiency reporting cannot hide recovery cost.

## Tool safety and verification

The host adapter should classify each exposed operation as read-only, reversible mutation, irreversible or public mutation, or consequential mutation. It should also expose, when possible, target scope, idempotency support, rollback path, required approval, and artifact/state revision. If it cannot classify an operation reliably, treat it as potentially consequential.

Use read-only tools for evidence first. Before any mutation, apply the core skill's preflight, exact-payload confirmation, single-executor, and post-state verification rules. A worker never gains mutation authority merely because it can call a tool.

Choose verification by risk and artifact type. Low-risk deterministic work may use automated checks and supervisor evidence review. Coupled, creative, externally visible, high-impact, regulated, or safety-sensitive work needs the stronger review stated in the task contract, including independent or qualified review when required. Do not run a ceremonial review: it must inspect the artifact and acceptance evidence without inheriting the producer's conclusion.

## Extending a host or domain

To add a worker type, define its capability floor, contract inputs, non-overlapping ownership, output schema, checks, escalation path, and minimum evidence. To add a tool adapter, document only the host-provided capabilities, read/mutate classification, authorization requirements, failure behavior, artifact revisions, and available telemetry. To add an evaluation, create a deterministic fixture and paired baseline case that tests the new rule without claiming a runtime integration that does not exist.

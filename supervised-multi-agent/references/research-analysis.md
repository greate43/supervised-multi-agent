# Research and analysis

Use this reference for factual research, comparisons, recommendations, investigations, calculations, and data analysis.

## Team shape

- Evidence workers: investigate independent questions, sources, datasets, or hypotheses.
- Analyst: combine evidence, perform calculations, and develop the reasoning chain.
- Skeptical reviewer: look for unsupported claims, conflicting evidence, missing alternatives, calculation errors, and stale information.
- Synthesizer: produce a draft synthesis and evidence map from verified evidence and resolved disagreements for supervisor verification.

Use independent lanes only when they cover distinct questions or provide valuable corroboration.

## Worker readiness

Before research or analysis, give the worker the exact question, scope, freshness rule, source hierarchy, comparison criteria, uncertainty standard, evidence-ledger format, and assigned calculation or provenance checks. Before `READY_FOR_REVIEW`, it must self-review every material claim against current evidence, inspect conflicts and alternative explanations, and run available assigned checks for source dates, schema or data integrity, formulas, units, denominators, and reproducibility. Unsupported or stale claims, unresolved material conflicts, calculation failures, or missing provenance prevent a ready status. Deterministic failures return for focused correction before synthesis, while passing checks still require skeptical supervisor review of reasoning and conclusions.

## Supervisor review gate

Before accepting worker research or analysis, freeze the question, scope, freshness rule, comparison criteria, evidence ledger, calculations, and submitted synthesis. Trace every material conclusion to a valid source, dataset, or reproducible calculation; check that quotations and values preserve context; test units, assumptions, conflicts, uncertainty, and the strongest credible alternative explanation. Do not accept source count, confident prose, or worker consensus as proof.

Return `REPAIR_REQUIRED` for unsupported claims, stale or weak sources where stronger authority is required, calculation errors, omitted material conflicts, or recommendations that do not follow from the user's constraints. Return `BLOCKED` when decisive evidence or required specialist judgment is unavailable. Accept only when every required criterion passes with claim-level provenance and reproducible evidence; keep judgment and unknowns labeled rather than converting them into facts.

## Quality gate

Define the decision or question, scope, freshness requirements, source hierarchy, comparison criteria, and uncertainty standard. Prefer primary and authoritative sources when available. Distinguish sourced fact, calculation, inference, judgment, and unknown.

Maintain an evidence ledger containing claim, source or dataset, date, relevant excerpt or value, confidence, and conflicts. Reproduce important calculations and check units, assumptions, denominators, and edge cases. Resolve contradictory evidence explicitly rather than averaging it away.

The reviewer should test the strongest alternative explanation and verify that recommendations follow from the user's constraints. High-stakes conclusions require stronger sources and review proportional to consequence. Cite or link sources for material external claims and recommendations in user-facing output unless the user requests citation-free output, the source is private, or the format cannot support citations; retain provenance in the evidence ledger in every case.

## Token efficiency

Partition queries before searching, deduplicate sources, and record reusable evidence once. Workers return claim-level findings rather than raw page dumps. Re-search only when evidence is missing, conflicting, stale, or invalidated by a scope change.

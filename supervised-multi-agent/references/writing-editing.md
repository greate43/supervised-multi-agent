# Writing and editorial work

Use this reference for drafting, rewriting, copyediting, documentation, scripts, reports, presentations, and content design.

## Team shape

Choose roles according to the work:

- Researcher or source checker: collect and verify claims, terminology, quotations, and citations.
- Drafter: create the piece from the approved brief and outline.
- Developmental editor: review argument, structure, completeness, audience fit, and narrative flow.
- Copyeditor or fact checker: review clarity, consistency, grammar, style, and factual accuracy.

For small pieces, combine roles. Require independent final review only when the user, governing instructions, consequence of error, or external-publication risk demands it; otherwise use the core review fallback appropriate to the host.

## Worker readiness

Before drafting or editing, give the worker the canonical brief, audience, purpose, source ledger, voice and meaning-preservation constraints, style and format requirements, and assigned checks. Before `READY_FOR_REVIEW`, it must self-review the current artifact against that complete slice and run available assigned checks such as factual-claim coverage, citations and links, spelling or style, cross-references, accessibility, and format validation. A known unsupported claim, changed meaning, missing section, failed check, or stale check result prevents a ready status; report the concern or block instead. Deterministic failures should return directly for focused correction, while a passing worker artifact still requires the supervisor's editorial and factual review.

## Supervisor review gate

Before accepting a material worker draft or edit, freeze the canonical brief, source ledger, prior accepted revision, and worker artifact. Review the artifact itself rather than the worker's summary. Grade the applicable criteria for factual support, argument and structure, completeness, audience and purpose, preservation of meaning and voice, required style and format, originality, accessibility, grammar, and cross-reference consistency. Verify changed factual claims against their sources and inspect enough surrounding text to catch contradictions or damage outside the edited passage.

Return `REPAIR_REQUIRED` when any required criterion fails, a material claim is unsupported, or an edit changes intended meaning; return `BLOCKED` when required sources, rights, subject-matter judgment, or accountable approval are unavailable. Accept only when every required criterion passes with artifact or source evidence. Keep optional stylistic preferences separate from defects.

## Quality gate

Define audience, purpose, desired action, voice, format, length, required facts, prohibited claims, and source rules before drafting. Keep one canonical brief and outline.

Review the final piece for factual accuracy, logical coherence, structure, completeness, clarity, tone, terminology, evidence, originality, accessibility, grammar, and formatting. Preserve the author's intended meaning and distinctive voice. Do not compress nuance merely to reduce tokens or word count.

Reviewers should identify precise issues and propose bounded changes. Rewrite the whole artifact only when its structure is fundamentally wrong or the user requests a full rewrite. Re-check altered claims and cross-references after revision.

## Token efficiency

Share the canonical brief, outline, source ledger, and current artifact instead of the full conversation. Use comments or change lists for review passes, then send only the revised sections and affected dependencies. Do not make multiple agents summarize the same sources unless independent verification is valuable.

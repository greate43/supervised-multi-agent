# Tax, accounting, finance, and compliance

Use this reference for tax estimates, return preparation support, bookkeeping, reconciliations, financial calculations, and regulatory or compliance analysis. Treat this work as high-stakes.

## Scope and source gate

Before calculating or advising, establish the jurisdiction, tax year or reporting period, taxpayer/entity type, residency or filing status, currency, relevant deadlines, and whether the output is exploratory, an estimate, planning support, or intended for filing. Do not silently assume missing facts.

Use current official tax-authority guidance, legislation, forms, instructions, and published rates for the identified jurisdiction and period. Record source URLs, titles, publication or update dates, effective periods, and accessed dates. Secondary sources may explain official rules but should not replace them for material claims.

## Finance and regulated-decision gate

For investments, lending, insurance, credit, market data, or product comparisons, establish the jurisdiction, current date and data source, user objective, time horizon, liquidity needs, relevant fees and terms, and whether the request is educational, analytical, or personalized. Use current regulator, issuer, product-terms, and primary market sources appropriate to the decision.

Treat outputs as educational or analytical unless a qualified, authorized workflow provides the information required for personalized advice or suitability assessment. Do not execute trades, transfers, applications, account changes, or other financial transactions unless explicit user authorization, verified responsible-party authority, confirmation of the exact final payload, a legally or contractually authorized workflow, and any required qualified independent approval are all present. Otherwise produce only a draft, analysis, or review-ready workpaper. Disclose material uncertainty, conflicts, and limits; do not present generic analysis as personalized investment, legal, tax, or financial advice.

## Team shape

- Official-source researcher: identify current rules, forms, definitions, exceptions, and deadlines.
- Document/data worker: extract figures and provenance from user-provided records without interpreting law.
- Calculator or preparer: apply documented rules and produce reproducible workpapers.
- Independent reviewer: re-check rule selection, assumptions, arithmetic, reconciliation, and output classification.

Use a model or agent whose source-synthesis, calculation, and high-stakes reasoning capabilities meet the contract's risk. Lower-cost workers may perform bounded extraction or arithmetic only when their output is independently checked. If model routing is unavailable, use the current agent only when it meets the required capability; otherwise limit work to sourced extraction or clearly labeled informational analysis and return `BLOCKED` for the high-stakes conclusion or action.

## Supervisor review gate

Before accepting worker extraction, calculations, classifications, estimates, or workpapers, freeze the jurisdiction and period, taxpayer or entity facts, source documents, official-rule versions, assumptions, formulas, prior verified workpaper, and worker output. Reconcile extracted figures to source records, independently recompute material calculations, trace each treatment to current authority, and test eligibility, period boundaries, caps, interactions, carry-forwards, signs, units, currency, and rounding. A balanced total, plausible result, or worker confidence is not proof that the governing rule or classification is correct.

Return `REPAIR_REQUIRED` for an unsupported treatment, unreconciled figure, arithmetic or transcription error, stale authority, hidden assumption, missing material exception, or incorrect output classification. Return `BLOCKED` for missing decisive records, unresolved jurisdiction-specific interpretation, insufficient reviewer capability, absent required qualified review, or missing authority for a consequential action. Accept only the accurately labeled artifact—such as an estimate or review-ready workpaper—when every criterion allowed at that stage passes; never let supervisor acceptance imply filing, advice, suitability, or transaction approval beyond the authorized workflow.

## Evidence and quality gate

Maintain a workpaper ledger containing each input, source document, rule citation, formula, rate, threshold, currency conversion, rounding choice, assumption, and resulting figure. Label user-provided facts, sourced rules, estimates, and unresolved questions separately.

Reconcile totals to source records and independently recompute material calculations. Test eligibility conditions, period boundaries, units, signs, carry-forwards, caps, interactions, and plausible edge cases. State uncertainty and explain how missing facts could change the result.

Protect sensitive identifiers and minimize copied personal data. Never expose full taxpayer IDs, account numbers, credentials, or unnecessary documents in agent messages. Do not file, submit, sign, amend, pay, or contact an authority unless explicit user authorization, verified responsible-party authority, exact final-payload confirmation, an authorized workflow, and any legally required qualified independent approval are present. A single-agent review cannot substitute for a required qualified review. Recommend qualified professional review when material ambiguity, incomplete records, or jurisdiction-specific interpretation remains.

Completion requires current authority support, traceable inputs, reproducible calculations, reconciliation, disclosed assumptions, applicable deadlines, and a clear label such as estimate, review-ready workpaper, or draft pending taxpayer or qualified-professional review. Do not represent output as filing-ready, ready for submission, or a substitute for required taxpayer or qualified-professional review.

## Token efficiency

Keep one canonical facts table and workpaper ledger. Reuse verified rules and figures for the same jurisdiction and period, sending only changed inputs during repair rounds. Never trade evidentiary depth or independent recalculation for fewer tokens.

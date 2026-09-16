# Worker review fixture

Review stage: worker output before integration.

- Worker head: `f7a8b9c`
- Worker status: `READY_FOR_REVIEW`
- Changed file: `adapter.py`
- Worker-reported check: none.
- Supervisor-verified base: unavailable.
- Required external API schema: referenced by the worker but unavailable.

## Assigned acceptance slice

1. Preserve the existing adapter's public field mapping.
2. Accept every required field in the current external API schema.
3. Reject unknown fields only when the existing compatibility contract requires it.

Review the supplied worker file without editing or integrating it. Do not infer the missing base implementation or API schema.

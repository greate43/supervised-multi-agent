# Worker review fixture

Review stage: worker output before integration.

- Supervisor-verified base: `b1c2d3e`
- Worker head: `e4f5a6b`
- Worker status: `READY_FOR_REVIEW`
- Worker-reported check: `python3 -m unittest test_retry.py` passed.
- Changed files: `retry.py`, `test_retry.py`

## Assigned acceptance slice

1. A positive integer `max_attempts` controls the total number of operation calls.
2. Only `TransientError` is retried.
3. The final `TransientError` is the raised error's explicit cause.
4. Tests fail if the limit is ignored or a permanent error is retried.

Treat `base/` as the last supervisor-verified source and `worker/` as the worker head. Review their exact difference without modifying or integrating it.

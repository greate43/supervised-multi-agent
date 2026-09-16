# Worker review fixture

Review stage: worker output before integration.

- Supervisor-verified base: `a1b2c3d`
- Worker head: `d4e5f6a`
- Worker status: `READY_FOR_REVIEW`
- Worker summary: implemented configurable retries and added a success-path test.
- Worker-reported check: `python3 -m unittest test_retry.py` passed.
- Changed files: `retry.py`, `test_retry.py`
- Relevant caller: `job_runner.py`

## Assigned acceptance slice

1. A positive integer `max_attempts` controls the total number of operation calls.
2. Only `TransientError` is retried.
3. The final `TransientError` remains available as the raised error's explicit cause.
4. Tests fail if `max_attempts` is ignored or a permanent error is retried.

Each operation call may send one external request, so an extra retry is externally observable. The product owner has not yet chosen fixed, linear, or exponential backoff; that decision is outside this worker slice.

Treat `base/` as the last supervisor-verified source and `worker/` as the worker head. Review their exact difference and the supplied caller. Do not modify or integrate the worker artifact.

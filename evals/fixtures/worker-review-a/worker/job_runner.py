# Unchanged caller context.
from retry import run


def execute_job(send_request, request_limit):
    return run(send_request, max_attempts=request_limit)

# Supervisor-verified base revision.
class TransientError(Exception):
    pass


class PermanentError(Exception):
    pass


def run(operation, max_attempts=3):
    return operation()

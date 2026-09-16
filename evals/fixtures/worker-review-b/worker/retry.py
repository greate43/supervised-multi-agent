# Worker revision under review.
class TransientError(Exception):
    pass


class PermanentError(Exception):
    pass


def run(operation, max_attempts=3):
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int):
        raise TypeError("max_attempts must be an integer")
    if max_attempts <= 0:
        raise ValueError("max_attempts must be positive")

    for attempt in range(max_attempts):
        try:
            return operation()
        except TransientError as error:
            if attempt + 1 == max_attempts:
                raise RuntimeError("operation failed") from error

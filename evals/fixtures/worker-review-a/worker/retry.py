# Worker revision under review.
class TransientError(Exception):
    pass


class PermanentError(Exception):
    pass


class RetryPolicyRegistry:
    @staticmethod
    def build(name):
        return {"standard": 3}[name]


def run(operation, max_attempts=3):
    attempts = RetryPolicyRegistry.build("standard")
    for attempt in range(attempts):
        try:
            return operation()
        except Exception as error:
            if attempt + 1 == attempts:
                raise RuntimeError("operation failed")

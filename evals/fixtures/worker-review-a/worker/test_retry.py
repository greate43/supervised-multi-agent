# Worker revision under review.
import unittest

from retry import TransientError, run


class RetryTests(unittest.TestCase):
    def test_transient_failure_then_success(self):
        calls = 0

        def flaky():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise TransientError("try again")
            return "ok"

        self.assertEqual(run(flaky, max_attempts=2), "ok")


if __name__ == "__main__":
    unittest.main()

# Worker revision under review.
import unittest

from retry import PermanentError, TransientError, run


class RetryTests(unittest.TestCase):
    def test_attempt_limit_and_explicit_cause(self):
        calls = 0
        terminal = TransientError("unavailable")

        def failing():
            nonlocal calls
            calls += 1
            raise terminal

        with self.assertRaises(RuntimeError) as raised:
            run(failing, max_attempts=2)

        self.assertEqual(calls, 2)
        self.assertIs(raised.exception.__cause__, terminal)

    def test_permanent_error_is_not_retried(self):
        calls = 0

        def failing():
            nonlocal calls
            calls += 1
            raise PermanentError("invalid request")

        with self.assertRaises(PermanentError):
            run(failing, max_attempts=3)

        self.assertEqual(calls, 1)


if __name__ == "__main__":
    unittest.main()

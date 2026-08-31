import os
import time
import unittest

os.environ.setdefault("BOT_TOKEN", "test-token")

from bot.services import rate_limit


class RateLimitTests(unittest.TestCase):
    def setUp(self):
        self.old_period = rate_limit.RATE_LIMIT_PERIOD
        self.old_max = rate_limit.MAX_REQUESTS
        rate_limit.RATE_LIMIT_PERIOD = 100
        rate_limit.MAX_REQUESTS = 2
        rate_limit._cache = {}

    def tearDown(self):
        rate_limit.RATE_LIMIT_PERIOD = self.old_period
        rate_limit.MAX_REQUESTS = self.old_max
        rate_limit._cache = {}

    def test_allows_requests_until_limit(self):
        rate_limit._cache[10] = {"timestamps": [time.time() - 1]}
        allowed, remaining = rate_limit.can_send_request(10)
        self.assertTrue(allowed)
        self.assertEqual(remaining, 1)

    def test_rejects_when_limit_is_reached(self):
        rate_limit._cache[10] = {"timestamps": [time.time() - 2, time.time() - 1]}
        allowed, remaining = rate_limit.can_send_request(10)
        self.assertFalse(allowed)
        self.assertGreaterEqual(remaining, 0)

    def test_expired_timestamps_are_removed(self):
        rate_limit._cache[10] = {"timestamps": [time.time() - 101, time.time() - 1]}
        allowed, remaining = rate_limit.can_send_request(10)
        self.assertTrue(allowed)
        self.assertEqual(remaining, 1)


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("BOT_TOKEN", "test-token")

from bot.handlers import subscription


class SubscriptionCacheTests(unittest.TestCase):
    def setUp(self):
        self.old_ttl = subscription.MEMBERSHIP_CACHE_TTL_SECONDS
        subscription.MEMBERSHIP_CACHE_TTL_SECONDS = 300
        subscription.clear_membership_cache()

    def tearDown(self):
        subscription.MEMBERSHIP_CACHE_TTL_SECONDS = self.old_ttl
        subscription.clear_membership_cache()

    @patch.object(subscription.bot, "get_chat_member")
    def test_reuses_membership_result_within_ttl(self, get_chat_member):
        get_chat_member.return_value = SimpleNamespace(status="member")

        self.assertTrue(subscription.is_channel_member(42))
        self.assertTrue(subscription.is_channel_member(42))

        get_chat_member.assert_called_once()

    @patch.object(subscription.bot, "get_chat_member")
    def test_clear_cache_forces_fresh_api_check(self, get_chat_member):
        get_chat_member.return_value = SimpleNamespace(status="member")

        subscription.is_channel_member(42)
        subscription.clear_membership_cache(42)
        subscription.is_channel_member(42)

        self.assertEqual(get_chat_member.call_count, 2)

    @patch.object(subscription.bot, "get_chat_member")
    def test_caches_non_member_result_too(self, get_chat_member):
        get_chat_member.return_value = SimpleNamespace(status="left")

        self.assertFalse(subscription.is_channel_member(42))
        self.assertFalse(subscription.is_channel_member(42))

        get_chat_member.assert_called_once()


if __name__ == "__main__":
    unittest.main()

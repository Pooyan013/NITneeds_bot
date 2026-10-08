import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("BOT_TOKEN", "test-token")

from bot.handlers import requests


class RequestNotificationTests(unittest.TestCase):
    def test_timed_send_returns_telegram_result_and_logs_duration(self):
        result = SimpleNamespace(message_id=10)
        with patch.object(requests.bot, "send_message", return_value=result) as send, patch.object(
            requests.logger, "info"
        ) as log:
            actual = requests.timed_send_message(42, "hello", operation="test")

        self.assertIs(actual, result)
        send.assert_called_once_with(42, "hello")
        self.assertTrue(any("Telegram send operation=%s" in call.args[0] for call in log.call_args_list))

    def test_one_admin_failure_does_not_stop_other_notifications(self):
        request = {
            "request_id": "request-1",
            "message": "request text",
            "admin_messages": {},
        }
        sent = SimpleNamespace(message_id=99)

        def send_message(chat_id, text, **kwargs):
            if chat_id == 100:
                raise RuntimeError("chat not found")
            return sent

        with patch.object(requests.bot, "send_message", side_effect=send_message):
            requests._notify_admins(request, [100, 200], "sender")

        self.assertNotIn(100, request["admin_messages"])
        self.assertEqual(request["admin_messages"][200], 99)


if __name__ == "__main__":
    unittest.main()

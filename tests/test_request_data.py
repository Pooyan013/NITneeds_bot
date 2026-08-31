import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("BOT_TOKEN", "test-token")

from bot.handlers.requests import build_request


class RequestDataTests(unittest.TestCase):
    def test_request_text_is_trimmed_and_tagged(self):
        message = SimpleNamespace(
            chat=SimpleNamespace(id=42),
            message_id=7,
            text="  لپ‌تاپ برای فروش  ",
            from_user=SimpleNamespace(username="student", first_name="Ali", last_name="Test"),
        )
        request = build_request(message, "#فروشی")
        self.assertEqual(request["user_id"], 42)
        self.assertEqual(request["message"], "#فروشی\nلپ‌تاپ برای فروش")
        self.assertFalse(request["approved"])
        self.assertEqual(request["admin_messages"], {})
        self.assertTrue(request["request_id"])

    def test_request_category_has_question_prefix(self):
        message = SimpleNamespace(
            chat=SimpleNamespace(id=42),
            message_id=8,
            text="  یک سوال  ",
            from_user=SimpleNamespace(username=None, first_name="Ali", last_name=None),
        )
        request = build_request(message, "#درخواستی")
        self.assertEqual(request["message"], "❓یک سوال")


if __name__ == "__main__":
    unittest.main()

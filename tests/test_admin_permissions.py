import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("BOT_TOKEN", "test-token")

from bot.handlers import admin


class AdminPermissionTests(unittest.TestCase):
    def setUp(self):
        self.old_admin_ids = admin.ADMIN_IDS
        self.old_job_admin_id = admin.JOB_ADMIN_ID
        admin.ADMIN_IDS = {100, 200}
        admin.JOB_ADMIN_ID = 300

    def tearDown(self):
        admin.ADMIN_IDS = self.old_admin_ids
        admin.JOB_ADMIN_ID = self.old_job_admin_id

    def test_regular_request_is_managed_by_regular_admin(self):
        request = {"hashtag": "#فروشی"}
        self.assertTrue(admin._can_manage_request(100, request))
        self.assertFalse(admin._can_manage_request(300, request))

    def test_accept_callback_reaches_approval_handler(self):
        request = {
            "request_id": "request-1",
            "user_id": 500,
            "message": "#فروشی\nکتاب",
            "hashtag": "#فروشی",
            "approved": False,
            "username": "student",
            "admin_messages": {},
        }
        admin.pending_requests.clear()
        admin.pending_requests.append(request)
        call = SimpleNamespace(
            id="callback-1",
            data="accept_request-1",
            from_user=SimpleNamespace(id=100, username="admin"),
            message=SimpleNamespace(chat=SimpleNamespace(id=100)),
        )

        with patch.object(admin.bot, "answer_callback_query") as answer, patch.object(
            admin, "_approve_request"
        ) as approve:
            admin.handle_admin_action(call)

        answer.assert_called_once()
        approve.assert_called_once_with(request, call.from_user, 100)
        admin.pending_requests.clear()

    def test_unknown_request_is_acknowledged(self):
        admin.pending_requests.clear()
        call = SimpleNamespace(
            id="callback-2",
            data="accept_missing",
            from_user=SimpleNamespace(id=100, username="admin"),
            message=SimpleNamespace(chat=SimpleNamespace(id=100)),
        )

        with patch.object(admin.bot, "answer_callback_query") as answer:
            admin.handle_admin_action(call)

        answer.assert_called_once()
        self.assertIn("درخواست", answer.call_args.args[1])
    def test_job_request_is_managed_only_by_job_admin(self):
        request = {"hashtag": "#فرصت_شغلی"}
        self.assertTrue(admin._can_manage_request(300, request))
        self.assertFalse(admin._can_manage_request(100, request))


if __name__ == "__main__":
    unittest.main()


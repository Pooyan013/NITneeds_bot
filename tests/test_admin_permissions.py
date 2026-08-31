import os
import unittest

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

    def test_job_request_is_managed_only_by_job_admin(self):
        request = {"hashtag": "#فرصت_شغلی"}
        self.assertTrue(admin._can_manage_request(300, request))
        self.assertFalse(admin._can_manage_request(100, request))


if __name__ == "__main__":
    unittest.main()

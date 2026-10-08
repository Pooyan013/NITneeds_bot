import os
import unittest
from unittest.mock import patch

os.environ.setdefault("BOT_TOKEN", "test-token")

import main
from requests.exceptions import RequestException


class PollingTests(unittest.TestCase):
    def test_polling_retries_after_network_error(self):
        with patch.object(
            main.bot,
            "infinity_polling",
            side_effect=[RequestException("temporary failure"), KeyboardInterrupt],
        ) as polling, patch.object(main.time, "sleep") as sleep:
            main.run_polling()

        self.assertEqual(polling.call_count, 2)
        sleep.assert_called_once_with(main.POLLING_RETRY_DELAY_SECONDS)


if __name__ == "__main__":
    unittest.main()

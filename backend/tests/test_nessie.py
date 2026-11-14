import unittest
import urllib.error
from unittest.mock import patch

from backend.config import _load_id_map
from backend.nessie.client import NessieClient, NessieTransferUncertain
from backend.nessie import executor


class NessieTests(unittest.TestCase):
    def test_nessie_id_maps_must_be_json_objects_of_ids(self) -> None:
        with patch.dict("os.environ", {"TEST_NESSIE_MAP": '{"alex":"account-1"}'}):
            self.assertEqual(_load_id_map("TEST_NESSIE_MAP"), {"alex": "account-1"})
        with patch.dict("os.environ", {"TEST_NESSIE_MAP": "[]"}):
            with self.assertRaisesRegex(RuntimeError, "JSON object"):
                _load_id_map("TEST_NESSIE_MAP")

    def test_post_transport_failure_is_reported_as_uncertain(self) -> None:
        client = NessieClient.__new__(NessieClient)
        client.base_url = "https://api.reimaginebanking.com"
        with (
            patch("backend.nessie.client.NESSIE_API_KEY", "test-key"),
            patch("backend.nessie.client.urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")),
        ):
            with self.assertRaisesRegex(NessieTransferUncertain, "Check the Nessie transaction history"):
                client._request("/accounts/source/transfers", method="POST", body={"amount": 10})

    def test_transfer_without_receipt_is_not_mirrored_locally(self) -> None:
        client = unittest.mock.Mock()
        client.get_balance.return_value = 100
        client.create_transfer.return_value = {}
        with (
            patch.object(executor, "NESSIE_MODE", "nessie"),
            patch.object(executor, "NESSIE_ACCOUNT_MAP", {"alex": "source"}),
            patch.object(executor, "NESSIE_PAYEE_MAP", {"alex-electric": "destination"}),
            patch.object(executor, "NessieClient", return_value=client),
            patch.object(executor.db, "sync_account_balance"),
            patch.object(executor.db, "perform_transfer") as perform_transfer,
        ):
            with self.assertRaisesRegex(NessieTransferUncertain, "Check the Nessie transaction history"):
                executor.execute_transfer("alex", "alex-electric", 10, "test")
        perform_transfer.assert_not_called()


if __name__ == "__main__":
    unittest.main()

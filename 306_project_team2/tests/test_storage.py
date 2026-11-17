"""NFR-03: requests are saved and read back correctly."""
from helpdesk.models import Status
from tests.helpers import DataTestCase


class StorageTest(DataTestCase):
    def test_sample_data_loads(self):
        self.assertEqual(len(self.requests.all()), 8)
        self.assertEqual(len(self.users.all()), 7)

    def test_saved_change_survives_reload(self):
        r = self.requests.get("R-0001")
        r.title = "Lab PC 14 won't boot"
        self.requests.save(r)
        self.assertEqual(self.requests.get("R-0001").title, "Lab PC 14 won't boot")
        self.assertEqual(self.requests.get("R-0001").status, Status.SUBMITTED)

    def test_save_leaves_no_temporary_file(self):
        self.requests.save(self.requests.get("R-0001"))
        self.assertEqual(list(self.tmp.glob("*.tmp")), [])

    def test_next_id_follows_highest(self):
        self.assertEqual(self.requests.next_id(), "R-0009")

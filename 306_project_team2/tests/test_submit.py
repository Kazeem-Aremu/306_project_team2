"""FR-01 / Story 1: submit a request."""
import unittest

from helpdesk.models import Status
from helpdesk.request_service import ValidationError
from tests.helpers import DataTestCase



class SubmitTest(DataTestCase):
    def test_valid_submission_is_saved_as_submitted(self):
        r = self.service.submit(self.requester, "Mouse broken", "Left button dead.",
                                "Library, Room 101, PC 3", "Hardware", "Low")
        self.assertEqual(r.status, Status.SUBMITTED)
        self.assertEqual(self.requests.get(r.request_id).title, "Mouse broken")

    def test_missing_fields_are_all_named(self):
        with self.assertRaises(ValidationError) as e:
            self.service.submit(self.requester, "", "", "", "Hardware", "Low")
        for field in ("title", "description", "location"):
            self.assertIn(field, str(e.exception).lower())
        self.assertEqual(len(self.requests.all()), 8)  # nothing saved

    def test_title_over_100_characters_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.service.submit(self.requester, "x" * 101, "d", "loc", "Hardware", "Low")

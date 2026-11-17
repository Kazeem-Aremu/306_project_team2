"""FR-06 to FR-08 / Stories 2-4: notes, search and summary (Sprint 2)."""
import unittest

from helpdesk.models import NoteType
from helpdesk.report_service import ReportService
from tests.helpers import DataTestCase

TODO = "Sprint 2: remove once the method is built"


class NotesSearchSummaryTest(DataTestCase):
    @unittest.skip(TODO)
    def test_requester_sees_only_resolution_notes(self):
        notes = self.service.visible_notes(self.users.get("U-103"), "R-0006")
        self.assertTrue(all(n.type == NoteType.RESOLUTION for n in notes))

    @unittest.skip(TODO)
    def test_empty_note_rejected(self):
        with self.assertRaises(Exception):
            self.service.add_note(self.tech, "R-0003", "   ")

    @unittest.skip(TODO)
    def test_filters_combine(self):
        found = self.service.search(self.coordinator, status="Assigned", category="Network/Wi-Fi")
        self.assertEqual([r.request_id for r in found], ["R-0003"])

    @unittest.skip(TODO)
    def test_summary_counts_match_sample_data(self):
        counts = ReportService(self.requests.all()).count_open_closed()
        self.assertEqual(counts, {"Open": 5, "Closed": 2, "Cancelled": 1})

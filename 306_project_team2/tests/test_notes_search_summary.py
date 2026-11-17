"""FR-06 to FR-08 / Stories 2-4: notes, search and summary (Sprint 2)."""
import unittest

from helpdesk.models import NoteType
from helpdesk.report_service import ReportService
from tests.helpers import DataTestCase



class NotesSearchSummaryTest(DataTestCase):
    def test_requester_sees_only_resolution_notes(self):
        notes = self.service.visible_notes(self.users.get("U-103"), "R-0006")
        self.assertTrue(all(n.type == NoteType.RESOLUTION for n in notes))

    def test_empty_note_rejected(self):
        with self.assertRaises(Exception):
            self.service.add_note(self.tech, "R-0003", "   ")

    def test_filters_combine(self):
        found = self.service.search(self.coordinator, status="Assigned", category="Network/Wi-Fi")
        self.assertEqual([r.request_id for r in found], ["R-0003"])

    def test_summary_counts_match_sample_data(self):
        counts = ReportService(self.requests.all()).count_open_closed()
        self.assertEqual(counts, {"Open": 5, "Closed": 2, "Cancelled": 1})


class MoreNotesSearchSummaryTest(DataTestCase):
    def test_resolution_note_is_visible_to_requester(self):
        self.service.change_status(self.tech, "R-0003", "In Progress")
        self.service.add_note(self.tech, "R-0003", "Restarted the access point.")
        self.service.change_status(self.tech, "R-0003", "Resolved", resolution_note="Replaced the access point.")
        seen = self.service.visible_notes(self.users.get("U-103"), "R-0003")
        self.assertEqual([n.text for n in seen], ["Replaced the access point."])

    def test_admin_note_hidden_from_technician(self):
        self.service.add_note(self.coordinator, "R-0003", "Escalate if not fixed by Friday.")
        types = {n.type for n in self.service.visible_notes(self.tech, "R-0003")}
        self.assertNotIn(NoteType.ADMIN, types)

    def test_requester_cannot_add_notes(self):
        with self.assertRaises(Exception):
            self.service.add_note(self.requester, "R-0001", "Any update?")

    def test_technician_search_limited_to_own_assignments(self):
        found = self.service.search(self.tech)
        self.assertTrue(all(r.assignment.technician_id == "T-01" for r in found))

    def test_requester_cannot_search(self):
        with self.assertRaises(Exception):
            self.service.search(self.requester)

    def test_counts_by_technician_and_priority(self):
        report = ReportService(self.requests.all())
        self.assertEqual(report.count_by_technician(), {"Unassigned": 2, "T-01": 1, "T-02": 1, "T-03": 1})
        self.assertEqual(sum(report.count_by_priority().values()), 8)

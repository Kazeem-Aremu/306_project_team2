"""FR-02 to FR-05 / Stories 4-6: lists, review, assign, status changes."""
import unittest

from helpdesk.models import Status
from helpdesk.permissions import PermissionDenied
from helpdesk.request_service import TransitionError, ValidationError
from tests.helpers import DataTestCase

TODO = "Sprint 1: remove once the service method is built"


class WorkflowTest(DataTestCase):
    @unittest.skip(TODO)
    def test_requester_sees_only_own_requests(self):
        self.assertTrue(all(r.requester_id == "U-101" for r in self.service.list_for(self.requester)))

    @unittest.skip(TODO)
    def test_coordinator_sees_all(self):
        self.assertEqual(len(self.service.list_for(self.coordinator)), 8)

    @unittest.skip(TODO)
    def test_review_then_assign(self):
        self.service.review(self.coordinator, "R-0001", "Hardware", "High")
        r = self.service.assign(self.coordinator, "R-0001", "T-01")
        self.assertEqual(r.status, Status.ASSIGNED)
        self.assertEqual(r.assignment.technician_id, "T-01")

    @unittest.skip(TODO)
    def test_cannot_assign_submitted_request(self):
        with self.assertRaises(TransitionError):
            self.service.assign(self.coordinator, "R-0001", "T-01")

    @unittest.skip(TODO)
    def test_requester_cannot_assign(self):
        with self.assertRaises(PermissionDenied):
            self.service.assign(self.requester, "R-0002", "T-01")
        self.assertEqual(self.requests.get("R-0002").status, Status.REVIEWED)  # unchanged

    @unittest.skip(TODO)
    def test_resolve_needs_resolution_note(self):
        self.service.change_status(self.tech, "R-0003", "In Progress")
        with self.assertRaises(ValidationError):
            self.service.change_status(self.tech, "R-0003", "Resolved", resolution_note="")

    @unittest.skip(TODO)
    def test_other_technician_cannot_change_status(self):
        with self.assertRaises(PermissionDenied):
            self.service.change_status(self.other_tech, "R-0003", "In Progress")

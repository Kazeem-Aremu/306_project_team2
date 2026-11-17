"""FR-02 to FR-05 / Stories 4-6: lists, review, assign, status changes."""
import unittest

from helpdesk.models import Status
from helpdesk.permissions import PermissionDenied
from helpdesk.request_service import TransitionError, ValidationError
from tests.helpers import DataTestCase



class WorkflowTest(DataTestCase):
    def test_requester_sees_only_own_requests(self):
        self.assertTrue(all(r.requester_id == "U-101" for r in self.service.list_for(self.requester)))

    def test_coordinator_sees_all(self):
        self.assertEqual(len(self.service.list_for(self.coordinator)), 8)

    def test_review_then_assign(self):
        self.service.review(self.coordinator, "R-0001", "Hardware", "High")
        r = self.service.assign(self.coordinator, "R-0001", "T-01")
        self.assertEqual(r.status, Status.ASSIGNED)
        self.assertEqual(r.assignment.technician_id, "T-01")

    def test_cannot_assign_submitted_request(self):
        with self.assertRaises(TransitionError):
            self.service.assign(self.coordinator, "R-0001", "T-01")

    def test_requester_cannot_assign(self):
        with self.assertRaises(PermissionDenied):
            self.service.assign(self.requester, "R-0002", "T-01")
        self.assertEqual(self.requests.get("R-0002").status, Status.REVIEWED)  # unchanged

    def test_resolve_needs_resolution_note(self):
        self.service.change_status(self.tech, "R-0003", "In Progress")
        with self.assertRaises(ValidationError):
            self.service.change_status(self.tech, "R-0003", "Resolved", resolution_note="")

    def test_other_technician_cannot_change_status(self):
        with self.assertRaises(PermissionDenied):
            self.service.change_status(self.other_tech, "R-0003", "In Progress")


class MoreWorkflowTest(DataTestCase):
    """Extra cases from the stories and BR-1/BR-2."""

    def test_review_of_reviewed_request_changes_priority_only(self):
        r = self.service.review(self.coordinator, "R-0002", "Classroom AV", "Low")
        self.assertEqual(r.status, Status.REVIEWED)
        self.assertEqual(self.requests.get("R-0002").priority.value, "Low")

    def test_requester_can_cancel_own_submitted_request(self):
        r = self.service.change_status(self.requester, "R-0001", "Cancelled")
        self.assertEqual(r.status, Status.CANCELLED)

    def test_requester_cannot_cancel_someone_elses_request(self):
        with self.assertRaises(PermissionDenied):
            self.service.change_status(self.users.get("U-102"), "R-0001", "Cancelled")

    def test_requester_cannot_cancel_after_review(self):
        with self.assertRaises(TransitionError):
            self.service.change_status(self.users.get("U-102"), "R-0002", "Cancelled")

    def test_technician_cannot_close(self):
        with self.assertRaises(TransitionError):
            self.service.change_status(self.tech, "R-0006", "Closed")

    def test_full_lifecycle_to_closed(self):
        self.service.review(self.coordinator, "R-0001", "Hardware", "High")
        self.service.assign(self.coordinator, "R-0001", "T-01")
        self.service.change_status(self.tech, "R-0001", "In Progress")
        self.service.change_status(self.tech, "R-0001", "Resolved", resolution_note="Reseated the RAM.")
        r = self.service.change_status(self.coordinator, "R-0001", "Closed")
        self.assertEqual(r.status, Status.CLOSED)
        self.assertEqual([h.to_status for h in r.history][-5:],
                         [Status.REVIEWED, Status.ASSIGNED, Status.IN_PROGRESS, Status.RESOLVED, Status.CLOSED])

    def test_unassign_clears_technician(self):
        r = self.service.change_status(self.coordinator, "R-0003", "Reviewed")
        self.assertIsNone(r.assignment)

    def test_assign_to_non_technician_rejected(self):
        with self.assertRaises(ValidationError):
            self.service.assign(self.coordinator, "R-0002", "U-101")

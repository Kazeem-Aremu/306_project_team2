"""FR-05: allowed and disallowed status changes (BR-1, state diagram)."""
import unittest

from helpdesk.models import Role, Status
from helpdesk.status_rules import TRANSITIONS, allowed_next, can_transition


class StatusRulesTest(unittest.TestCase):
    def test_table_has_13_transitions_like_the_state_diagram(self):
        self.assertEqual(len(TRANSITIONS), 13)

    def test_coordinator_can_review_submitted(self):
        self.assertTrue(can_transition(Status.SUBMITTED, Status.REVIEWED, Role.COORDINATOR))

    def test_cannot_assign_before_review(self):
        self.assertFalse(can_transition(Status.SUBMITTED, Status.ASSIGNED, Role.COORDINATOR))

    def test_technician_cannot_close(self):
        self.assertFalse(can_transition(Status.RESOLVED, Status.CLOSED, Role.TECHNICIAN))

    def test_in_progress_cannot_jump_to_closed(self):
        for role in Role:
            self.assertFalse(can_transition(Status.IN_PROGRESS, Status.CLOSED, role))

    def test_closed_and_cancelled_are_final(self):
        for role in Role:
            self.assertEqual(allowed_next(Status.CLOSED, role), [])
            self.assertEqual(allowed_next(Status.CANCELLED, role), [])

    def test_requester_can_only_cancel_while_submitted(self):
        self.assertTrue(can_transition(Status.SUBMITTED, Status.CANCELLED, Role.REQUESTER))
        self.assertFalse(can_transition(Status.REVIEWED, Status.CANCELLED, Role.REQUESTER))


if __name__ == "__main__":
    unittest.main()

"""All business rules for requests. Called by the UI; calls the repositories.
Each method: (1) check permission, (2) validate, (3) change the request, (4) save.
On any failure, raise an exception and save nothing."""
from __future__ import annotations

from datetime import datetime

from helpdesk import permissions, status_rules
from helpdesk.models import CATEGORIES, DESCRIPTION_MAX, TITLE_MAX, Note, NoteType, Priority, Request, Status, User
from helpdesk.repositories import NoteRepository, RequestRepository, UserRepository


class ValidationError(Exception):
    """Input is missing or invalid. The message names every field that needs fixing."""


class TransitionError(Exception):
    """The status change is not in status_rules.TRANSITIONS."""


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class RequestService:
    def __init__(self, requests: RequestRepository | None = None,
                 notes: NoteRepository | None = None, users: UserRepository | None = None):
        self.requests = requests or RequestRepository()
        self.notes = notes or NoteRepository()
        self.users = users or UserRepository()

    # ---- Sprint 1 (Week 11) ----

    def submit(self, user: User, title: str, description: str, location: str,
               category: str, urgency: str) -> Request:
        """FR-01 / Story 1. Validate (title, description, location required; TITLE_MAX,
        DESCRIPTION_MAX; category in CATEGORIES; urgency a Priority), create the request
        with status Submitted, priority = urgency, one history entry, and save it.
        Raise ValidationError listing every problem at once."""
        raise NotImplementedError("FR-01: submit a request")

    def list_for(self, user: User) -> list[Request]:
        """FR-02 / Story 4. Requester: own requests. Technician: assigned to them.
        Coordinator: all. Newest first."""
        raise NotImplementedError("FR-02: role-based request list")

    def review(self, user: User, request_id: str, category: str, priority: str) -> Request:
        """FR-03 / Story 5. Coordinator confirms category and priority of a Submitted
        request; status becomes Reviewed."""
        raise NotImplementedError("FR-03: review, classify and prioritize")

    def assign(self, user: User, request_id: str, technician_id: str) -> Request:
        """FR-04 / Story 5 / sequence diagram. Only a Reviewed request can be assigned.
        Record Assignment(technician_id, assigned_by, assigned_at); status becomes Assigned."""
        raise NotImplementedError("FR-04: assign to technician")

    def change_status(self, user: User, request_id: str, new_status: str,
                      resolution_note: str | None = None) -> Request:
        """FR-05 / state diagram. Use status_rules.can_transition and
        permissions.require. Resolved requires a non-empty resolution_note
        (Story 6), saved as a RESOLUTION note. Add a StatusChange to history."""
        raise NotImplementedError("FR-05: change status")

    # ---- Sprint 2 (Week 12) ----

    def add_note(self, user: User, request_id: str, text: str) -> Note:
        """FR-06 / Story 2. Technician -> WORK note (own assignments only);
        Coordinator -> ADMIN note. Reject empty text."""
        raise NotImplementedError("FR-06: add a note")

    def visible_notes(self, user: User, request_id: str) -> list[Note]:
        """FR-06 / Story 4. Requesters see RESOLUTION notes only (scope item 6)."""
        raise NotImplementedError("FR-06: note visibility")

    def search(self, user: User, status: str | None = None, category: str | None = None,
               priority: str | None = None, requester_id: str | None = None,
               technician_id: str | None = None) -> list[Request]:
        """FR-07. Filters combine (AND). Technicians search only their own assignments."""
        raise NotImplementedError("FR-07: search and filter")

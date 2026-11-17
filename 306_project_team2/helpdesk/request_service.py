"""All business rules for requests. Called by web.py; calls the repositories.
Each method: (1) check permission, (2) validate, (3) change the request, (4) save.
On any failure, raise an exception and save nothing."""
from __future__ import annotations

from datetime import datetime

from helpdesk import permissions, status_rules
from helpdesk.models import (CATEGORIES, DESCRIPTION_MAX, TITLE_MAX, Assignment, Note, NoteType,
                             Priority, Request, Role, Status, StatusChange, User)
from helpdesk.repositories import NoteRepository, RequestRepository, UserRepository

NOTE_MAX = 1000
LOCATION_MAX = 120
LOCKED_FOR_WORK = {Status.RESOLVED, Status.CLOSED, Status.CANCELLED}


class ValidationError(Exception):
    """Input is missing or invalid. The message names every field that needs fixing."""


class TransitionError(Exception):
    """The status change is not in status_rules.TRANSITIONS."""


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _priority(value: str, field: str) -> Priority:
    try:
        return Priority(value)
    except ValueError:
        raise ValidationError(f"{field} must be one of: Low, Medium, High, Urgent.") from None


def _status(value: str) -> Status:
    try:
        return Status(value)
    except ValueError:
        raise ValidationError(f"'{value}' is not a status.") from None


def _category(value: str) -> str:
    if value not in CATEGORIES:
        raise ValidationError(f"Category must be one of: {', '.join(CATEGORIES)}.")
    return value


class RequestService:
    def __init__(self, requests: RequestRepository | None = None,
                 notes: NoteRepository | None = None, users: UserRepository | None = None):
        self.requests = requests or RequestRepository()
        self.notes = notes or NoteRepository()
        self.users = users or UserRepository()

    # ---- helpers ----

    def _get(self, request_id: str) -> Request:
        request = self.requests.get(request_id or "")
        if request is None:
            raise ValidationError(f"Request {request_id} was not found.")
        return request

    def _record(self, request: Request, user: User, new: Status) -> None:
        """Move to `new`, add it to the history and save."""
        stamp = now()
        request.history.append(StatusChange(request.status, new, user.user_id, stamp))
        request.status = new
        request.updated_at = stamp
        self.requests.save(request)

    def _check_transition(self, request: Request, new: Status, user: User) -> None:
        if not status_rules.can_transition(request.status, new, user.role):
            allowed = status_rules.allowed_next(request.status, user.role)
            hint = f" Allowed next: {', '.join(s.value for s in allowed)}." if allowed else ""
            raise TransitionError(
                f"A {user.role.value} can't move a request from {request.status.value} "
                f"to {new.value}.{hint}")

    # ---- Sprint 1 (Week 11) ----

    def submit(self, user: User, title: str, description: str, location: str,
               category: str, urgency: str) -> Request:
        """FR-01 / Story 1. Validates every field, then saves the request as Submitted."""
        permissions.require(user, "submit")
        title, description, location = (title or "").strip(), (description or "").strip(), (location or "").strip()
        problems = [f"{name} is required." for name, value in
                    (("Title", title), ("Description", description), ("Location", location)) if not value]
        if len(title) > TITLE_MAX:
            problems.append(f"Title must be {TITLE_MAX} characters or less.")
        if len(description) > DESCRIPTION_MAX:
            problems.append(f"Description must be {DESCRIPTION_MAX} characters or less.")
        if len(location) > LOCATION_MAX:
            problems.append(f"Location must be {LOCATION_MAX} characters or less.")
        if category not in CATEGORIES:
            problems.append("Choose a category.")
        if urgency not in [p.value for p in Priority]:
            problems.append("Choose an urgency.")
        if problems:
            raise ValidationError(" ".join(problems))
        stamp = now()
        request = Request(
            request_id=self.requests.next_id(), title=title, description=description,
            location=location, category=category, requested_urgency=Priority(urgency),
            priority=Priority(urgency), status=Status.SUBMITTED, requester_id=user.user_id,
            created_at=stamp, updated_at=stamp,
            history=[StatusChange(None, Status.SUBMITTED, user.user_id, stamp)])
        self.requests.save(request)
        return request

    def list_for(self, user: User) -> list[Request]:
        """FR-02 / Story 4. Requester: own requests. Technician: assigned to them.
        Coordinator: all. Most recently updated first."""
        visible = [r for r in self.requests.all() if permissions.owns(user, r)]
        return sorted(visible, key=lambda r: r.updated_at, reverse=True)

    def review(self, user: User, request_id: str, category: str, priority: str) -> Request:
        """FR-03 / Story 5. The coordinator confirms category and priority. A Submitted
        request becomes Reviewed; on a later open request only the values change."""
        request = self._get(request_id)
        permissions.require(user, "review", request)
        category, new_priority = _category(category), _priority(priority, "Priority")
        if request.status in (Status.CLOSED, Status.CANCELLED):
            raise TransitionError(f"Request {request.request_id} is {request.status.value} and can't be changed.")
        request.category, request.priority = category, new_priority
        if request.status == Status.SUBMITTED:
            self._check_transition(request, Status.REVIEWED, user)
            self._record(request, user, Status.REVIEWED)
        else:
            request.updated_at = now()
            self.requests.save(request)
        return request

    def assign(self, user: User, request_id: str, technician_id: str) -> Request:
        """FR-04 / Story 5 / sequence diagram. Only a Reviewed request can be assigned."""
        request = self._get(request_id)
        permissions.require(user, "assign", request)
        technician = self.users.get(technician_id or "")
        if technician is None or technician.role != Role.TECHNICIAN:
            raise ValidationError("Choose a technician from the list.")
        if request.status != Status.REVIEWED:
            raise TransitionError(f"Request {request.request_id} is {request.status.value}; "
                                  "it must be reviewed before it can be assigned.")
        self._check_transition(request, Status.ASSIGNED, user)
        request.assignment = Assignment(technician.user_id, user.user_id, now())
        self._record(request, user, Status.ASSIGNED)
        return request

    def change_status(self, user: User, request_id: str, new_status: str,
                      resolution_note: str | None = None) -> Request:
        """FR-05 / state diagram. Allowed only if status_rules allows it for this role and
        the request belongs to the user. Resolved needs a resolution note (Story 6)."""
        request = self._get(request_id)
        permissions.require(user, "change_status", request)
        new = _status(new_status)
        if new == Status.ASSIGNED:
            raise TransitionError("Use Assign to choose a technician.")
        self._check_transition(request, new, user)
        note_text = (resolution_note or "").strip()
        if new == Status.RESOLVED:
            if not note_text:
                raise ValidationError("A resolution note is required to resolve a request.")
            if len(note_text) > NOTE_MAX:
                raise ValidationError(f"Notes must be {NOTE_MAX} characters or less.")
        if request.status == Status.ASSIGNED and new == Status.REVIEWED:
            request.assignment = None  # unassign
        self._record(request, user, new)
        if new == Status.RESOLVED:
            self.notes.add(Note(self.notes.next_id(), request.request_id, NoteType.RESOLUTION,
                                note_text, user.user_id, now()))
        return request

    # ---- Sprint 2 (Week 12) ----

    def add_note(self, user: User, request_id: str, text: str) -> Note:
        """FR-06 / Story 2. Technician adds a WORK note to their own open assignment;
        coordinator adds an ADMIN note. Requesters cannot add notes."""
        request = self._get(request_id)
        if user.role == Role.TECHNICIAN:
            permissions.require(user, "add_work_note", request)
            note_type = NoteType.WORK
            if request.status in LOCKED_FOR_WORK:
                raise TransitionError(f"Request {request.request_id} is {request.status.value}; "
                                      "work notes are locked unless the coordinator reopens it.")
        else:
            permissions.require(user, "add_admin_note", request)
            note_type = NoteType.ADMIN
        text = (text or "").strip()
        if not text:
            raise ValidationError("Note text is required.")
        if len(text) > NOTE_MAX:
            raise ValidationError(f"Notes must be {NOTE_MAX} characters or less.")
        note = Note(self.notes.next_id(), request.request_id, note_type, text, user.user_id, now())
        self.notes.add(note)
        request.updated_at = note.created_at
        self.requests.save(request)
        return note

    def visible_notes(self, user: User, request_id: str) -> list[Note]:
        """FR-06 / Story 4. Only the notes this user may see; requesters see resolution notes only."""
        request = self._get(request_id)
        permissions.require(user, "view_request", request)
        return [n for n in self.notes.for_request(request.request_id) if n.is_visible_to(user, request)]

    def search(self, user: User, status: str | None = None, category: str | None = None,
               priority: str | None = None, requester_id: str | None = None,
               technician_id: str | None = None) -> list[Request]:
        """FR-07 / Story 7. Filters combine (AND). Technicians search only their own assignments."""
        permissions.require(user, "search")
        wanted_status = _status(status) if status else None
        wanted_priority = _priority(priority, "Priority") if priority else None
        if category:
            _category(category)
        results = []
        for r in self.requests.all():
            if not permissions.owns(user, r):
                continue
            if wanted_status and r.status != wanted_status:
                continue
            if category and r.category != category:
                continue
            if wanted_priority and r.priority != wanted_priority:
                continue
            if requester_id and r.requester_id != requester_id:
                continue
            if technician_id and (r.assignment is None or r.assignment.technician_id != technician_id):
                continue
            results.append(r)
        return sorted(results, key=lambda r: r.updated_at, reverse=True)

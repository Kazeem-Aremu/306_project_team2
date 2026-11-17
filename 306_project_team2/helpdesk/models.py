"""Domain classes shared by every layer. Matches the class diagram (docs/models/04_class.png)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Role(str, Enum):
    REQUESTER = "Requester"
    COORDINATOR = "Coordinator"
    TECHNICIAN = "Technician"  # called "service staff" in the guide


class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class Status(str, Enum):
    SUBMITTED = "Submitted"
    REVIEWED = "Reviewed"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    WAITING = "Waiting"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"


OPEN_STATUSES = {Status.SUBMITTED, Status.REVIEWED, Status.ASSIGNED, Status.IN_PROGRESS, Status.WAITING}
CLOSED_STATUSES = {Status.RESOLVED, Status.CLOSED}  # confirm with instructor (open question 2)


class NoteType(str, Enum):
    WORK = "Work"            # technician, internal
    ADMIN = "Admin"          # coordinator, internal
    RESOLUTION = "Resolution"  # technician when resolving; requester can see it


CATEGORIES = ["Hardware", "Classroom AV", "Network/Wi-Fi", "Software", "Account/Access", "Other"]

TITLE_MAX = 100
DESCRIPTION_MAX = 1000


@dataclass
class User:
    user_id: str
    name: str
    role: Role


@dataclass
class Assignment:
    technician_id: str
    assigned_by: str
    assigned_at: str  # ISO 8601 timestamp


@dataclass
class StatusChange:
    from_status: Status | None
    to_status: Status
    changed_by: str
    changed_at: str


@dataclass
class Request:
    request_id: str
    title: str
    description: str
    location: str
    category: str
    requested_urgency: Priority
    priority: Priority
    status: Status
    requester_id: str
    created_at: str
    updated_at: str
    assignment: Assignment | None = None
    history: list[StatusChange] = field(default_factory=list)

    def is_open(self) -> bool:
        return self.status in OPEN_STATUSES


@dataclass
class Note:
    note_id: str
    request_id: str
    type: NoteType
    text: str
    author_id: str
    created_at: str

    def is_visible_to(self, user: User, request: Request) -> bool:
        """FR-06 / BR-3: resolution notes are visible to anyone who can see the request;
        work notes to the coordinator and the assigned technician; admin notes to the
        coordinator only. Requesters never see work or admin notes (scope item 6)."""
        if self.type == NoteType.RESOLUTION:
            return True
        if user.role == Role.COORDINATOR:
            return True
        if self.type == NoteType.WORK and user.role == Role.TECHNICIAN:
            return request.assignment is not None and request.assignment.technician_id == user.user_id
        return False

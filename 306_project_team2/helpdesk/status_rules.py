"""Allowed status changes (BR-1). This table is the single source of truth:
the state diagram, request_service.change_status and the tests all follow it.
Changing a rule means changing one row here (and the state diagram)."""
from helpdesk.models import Role, Status

S, R = Status, Role

# (from_status, to_status): roles allowed to make the change
TRANSITIONS: dict[tuple[Status, Status], set[Role]] = {
    (S.SUBMITTED, S.REVIEWED): {R.COORDINATOR},
    (S.SUBMITTED, S.CANCELLED): {R.COORDINATOR, R.REQUESTER},  # requester: own request only
    (S.REVIEWED, S.ASSIGNED): {R.COORDINATOR},
    (S.REVIEWED, S.CANCELLED): {R.COORDINATOR},
    (S.ASSIGNED, S.IN_PROGRESS): {R.TECHNICIAN},                # assigned technician only
    (S.ASSIGNED, S.REVIEWED): {R.COORDINATOR},                  # unassign
    (S.ASSIGNED, S.CANCELLED): {R.COORDINATOR},
    (S.IN_PROGRESS, S.WAITING): {R.TECHNICIAN},
    (S.IN_PROGRESS, S.RESOLVED): {R.TECHNICIAN},                # resolution note required
    (S.WAITING, S.IN_PROGRESS): {R.TECHNICIAN},
    (S.WAITING, S.CANCELLED): {R.COORDINATOR},
    (S.RESOLVED, S.CLOSED): {R.COORDINATOR},
    (S.RESOLVED, S.IN_PROGRESS): {R.COORDINATOR},               # reopen
}


def can_transition(current: Status, new: Status, role: Role) -> bool:
    """True if `role` may move a request from `current` to `new` (FR-05).
    Ownership (own request / own assignment) is checked in permissions.py."""
    return role in TRANSITIONS.get((current, new), set())


def allowed_next(current: Status, role: Role) -> list[Status]:
    """Statuses this role may choose next; the UI uses it to show only valid options."""
    return [to for (frm, to), roles in TRANSITIONS.items() if frm == current and role in roles]

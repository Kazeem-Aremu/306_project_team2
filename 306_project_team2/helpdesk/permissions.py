"""Role and ownership checks (BR-2, NFR-02). Every service method that changes data
calls `require` first, so hiding a button in the page is never the only protection."""
from helpdesk.models import Request, Role, User

ALL_ROLES = {Role.REQUESTER, Role.COORDINATOR, Role.TECHNICIAN}

# action name: roles allowed
ROLE_ACTIONS: dict[str, set[Role]] = {
    "submit": {Role.REQUESTER},
    "view_request": ALL_ROLES,
    "review": {Role.COORDINATOR},
    "classify": {Role.COORDINATOR},
    "assign": {Role.COORDINATOR},
    "change_status": ALL_ROLES,  # which change is allowed is decided by status_rules
    "add_work_note": {Role.TECHNICIAN},
    "add_admin_note": {Role.COORDINATOR},
    "search": {Role.COORDINATOR, Role.TECHNICIAN},
    "view_summary": {Role.COORDINATOR},
}


class PermissionDenied(Exception):
    """Raised when a user tries an action their role or ownership does not allow."""


def owns(user: User, request: Request) -> bool:
    """Requesters own the requests they submitted; technicians own requests assigned to
    them; the coordinator can act on every request."""
    if user.role == Role.COORDINATOR:
        return True
    if user.role == Role.REQUESTER:
        return request.requester_id == user.user_id
    return request.assignment is not None and request.assignment.technician_id == user.user_id


def can(user: User, action: str, request: Request | None = None) -> bool:
    """NFR-02: True if the user's role may take `action` and, when a request is given,
    the request belongs to them."""
    if user.role not in ROLE_ACTIONS.get(action, set()):
        return False
    return request is None or owns(user, request)


def require(user: User, action: str, request: Request | None = None) -> None:
    """Raise PermissionDenied with a plain-language reason if `can` is False."""
    if user.role not in ROLE_ACTIONS.get(action, set()):
        raise PermissionDenied(f"{user.role.value}s are not allowed to {action.replace('_', ' ')}.")
    if request is not None and not owns(user, request):
        whose = "assigned to you" if user.role == Role.TECHNICIAN else "one you submitted"
        raise PermissionDenied(f"You can only do that on a request that is {whose}.")

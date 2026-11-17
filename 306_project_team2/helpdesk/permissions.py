"""Role and ownership checks (BR-2, NFR-02). Every service method that changes data
calls `require` first, so hiding a menu option is never the only protection."""
from helpdesk.models import Request, Role, User

# action name: roles allowed
ROLE_ACTIONS: dict[str, set[Role]] = {
    "submit": {Role.REQUESTER},
    "review": {Role.COORDINATOR},
    "classify": {Role.COORDINATOR},
    "assign": {Role.COORDINATOR},
    "add_work_note": {Role.TECHNICIAN},
    "add_admin_note": {Role.COORDINATOR},
    "search": {Role.COORDINATOR, Role.TECHNICIAN},
    "view_summary": {Role.COORDINATOR},
}


class PermissionDenied(Exception):
    """Raised when a user tries an action their role or ownership does not allow."""


def can(user: User, action: str, request: Request | None = None) -> bool:
    """TODO (NFR-02): check the role against ROLE_ACTIONS, then ownership:
    - a requester may only act on requests where request.requester_id == user.user_id
    - a technician may only act on requests assigned to them
    """
    raise NotImplementedError("NFR-02: role and ownership checks")


def require(user: User, action: str, request: Request | None = None) -> None:
    """Raise PermissionDenied with a plain-language reason if `can` is False."""
    if not can(user, action, request):
        raise PermissionDenied(f"{user.role.value}s are not allowed to {action.replace('_', ' ')}.")

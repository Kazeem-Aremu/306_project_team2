"""Console interface (NFR-01). Shows menus and results only: no business rules here.
Matches the UI design (docs/models/08_ui_design.png)."""
from __future__ import annotations

from helpdesk.models import Role, User
from helpdesk.permissions import PermissionDenied
from helpdesk.report_service import ReportService
from helpdesk.repositories import UserRepository
from helpdesk.request_service import RequestService, TransitionError, ValidationError

MENUS: dict[Role, list[tuple[str, str]]] = {
    Role.REQUESTER: [("1", "Submit a request"), ("2", "View my requests"),
                     ("3", "View status and resolution"), ("4", "Cancel a Submitted request")],
    Role.COORDINATOR: [("1", "View all requests"), ("2", "Review: category, priority"),
                       ("3", "Assign a technician"), ("4", "Close, cancel or reopen"),
                       ("5", "Add admin note"), ("6", "Search / filter"), ("7", "Activity summary")],
    Role.TECHNICIAN: [("1", "View my assignments"), ("2", "Start, wait or resume work"),
                      ("3", "Add work note"), ("4", "Resolve with resolution note")],
}


def choose(prompt: str, options: list[str]) -> int:
    """Ask until the user types a valid number. Returns a 0-based index, or -1 for 0 (back)."""
    while True:
        answer = input(f"{prompt}: ").strip()
        if answer == "0":
            return -1
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer) - 1
        print(f"Please type a number from 1 to {len(options)}, or 0 to go back.")


def pick_user(users: UserRepository) -> User | None:
    print("\nChoose your role:  1 Requester   2 Coordinator   3 Technician   (0 to quit)")
    roles = [Role.REQUESTER, Role.COORDINATOR, Role.TECHNICIAN]
    r = choose("Role", [x.value for x in roles])
    if r == -1:
        return None
    people = [u for u in users.all() if u.role == roles[r]]
    for i, u in enumerate(people, 1):
        print(f"  {i}  {u.name} ({u.user_id})")
    p = choose("Sample user", [u.name for u in people])
    return None if p == -1 else people[p]


def run_menu(user: User, service: RequestService) -> None:
    items = MENUS[user.role]
    while True:
        print(f"\n{user.role.value} menu - {user.name}")
        for key, label in items:
            print(f"  {key}  {label}")
        print("  0  Switch role")
        i = choose("Choice", [label for _, label in items])
        if i == -1:
            return
        try:
            handle(user, items[i][1], service)
        except (ValidationError, PermissionDenied, TransitionError) as e:
            print(f"Not done: {e}")
        except NotImplementedError as e:
            print(f"Not built yet ({e}).")


def handle(user: User, choice: str, service: RequestService) -> None:
    """TODO (Sprint 1-2): ask for the inputs each choice needs, call the matching
    RequestService / ReportService method, and print the result.
    Example for 'Activity summary':
        print(ReportService(service.requests.all()).count_open_closed())"""
    if choice == "Activity summary":
        print(ReportService(service.requests.all()).count_open_closed())
        return
    if choice in ("View my requests", "View all requests", "View my assignments"):
        for r in service.list_for(user):
            print(f"{r.request_id}  {r.title[:30]:30}  {r.status.value:12}  {r.priority.value}")
        return
    raise NotImplementedError(f"menu option '{choice}'")


def main() -> None:
    print("Campus Technology Help Desk (prototype, simulated data)")
    users, service = UserRepository(), RequestService()
    while (user := pick_user(users)) is not None:
        run_menu(user, service)
    print("Goodbye.")

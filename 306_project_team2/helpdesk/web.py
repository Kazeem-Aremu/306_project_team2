"""Browser interface (NFR-01). A small local web server, built only from Python's standard
library, that serves the page in helpdesk/static/ and a JSON API over the services.

Interface layer only: no business rules here. Every action is passed to RequestService or
ReportService, and their errors are turned into messages the page shows.
Runs on 127.0.0.1 (this computer only); no internet connection is needed."""
from __future__ import annotations

import json
import threading
import webbrowser
from dataclasses import asdict, is_dataclass
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from helpdesk import permissions, status_rules
from helpdesk.models import CATEGORIES, Priority, Role, Status
from helpdesk.permissions import PermissionDenied
from helpdesk.report_service import ReportService
from helpdesk.request_service import RequestService, TransitionError, ValidationError

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_FILES = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
                "/style.css": ("style.css", "text/css")}


class NotFound(Exception):
    pass


def to_json(value):
    """Turn dataclasses and enums into plain JSON values."""
    if is_dataclass(value):
        return to_json(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: to_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json(v) for v in value]
    return value


class HelpDeskApi:
    """Maps each page action to one service call. Kept separate from the HTTP code so it
    can be tested directly."""

    def __init__(self, service: RequestService | None = None):
        self.service = service or RequestService()

    def user(self, user_id: str | None):
        u = self.service.users.get(user_id or "")
        if u is None:
            raise NotFound("Choose a user first.")
        return u

    def get_request(self, request_id: str | None):
        r = self.service.requests.get(request_id or "")
        if r is None:
            raise NotFound(f"Request {request_id} was not found.")
        return r

    # ---- reads ----
    def meta(self, q):
        techs = [u for u in self.service.users.all() if u.role == Role.TECHNICIAN]
        return {"categories": CATEGORIES, "priorities": [p.value for p in Priority],
                "statuses": [s.value for s in Status], "technicians": techs}

    def users(self, q):
        return self.service.users.all()

    def requests(self, q):
        return self.service.list_for(self.user(q.get("user")))

    def search(self, q):
        filters = {k: q.get(k) or None for k in ("status", "category", "priority",
                                                  "requester_id", "technician_id")}
        return self.service.search(self.user(q.get("user")), **filters)

    def detail(self, q):
        """One request with the notes this user may see and the statuses they may choose next."""
        user, req = self.user(q.get("user")), self.get_request(q.get("id"))
        permissions.require(user, "view_request", req)
        notes = self.service.visible_notes(user, req.request_id)
        return {"request": req, "notes": notes, "notes_message": None,
                "allowed_next": status_rules.allowed_next(req.status, user.role)}

    def summary(self, q):
        permissions.require(self.user(q.get("user")), "view_summary")
        report = ReportService(self.service.requests.all())
        return {"open_closed": report.count_open_closed(), "by_category": report.count_by_category(),
                "by_priority": report.count_by_priority(), "by_technician": report.count_by_technician()}

    # ---- actions ----
    def submit(self, b):
        return self.service.submit(self.user(b.get("user")), b.get("title", ""), b.get("description", ""),
                                   b.get("location", ""), b.get("category", ""), b.get("urgency", ""))

    def review(self, b):
        return self.service.review(self.user(b.get("user")), b.get("id"), b.get("category", ""),
                                   b.get("priority", ""))

    def assign(self, b):
        return self.service.assign(self.user(b.get("user")), b.get("id"), b.get("technician_id", ""))

    def status(self, b):
        return self.service.change_status(self.user(b.get("user")), b.get("id"), b.get("status", ""),
                                          b.get("resolution_note"))

    def note(self, b):
        return self.service.add_note(self.user(b.get("user")), b.get("id"), b.get("text", ""))


GET_ROUTES = {"/api/meta": "meta", "/api/users": "users", "/api/requests": "requests",
              "/api/search": "search", "/api/request": "detail", "/api/summary": "summary"}
POST_ROUTES = {"/api/submit": "submit", "/api/review": "review", "/api/assign": "assign",
               "/api/status": "status", "/api/note": "note"}
ERRORS = [(ValidationError, 400), (PermissionDenied, 403), (NotFound, 404), (TransitionError, 409),
          (NotImplementedError, 501)]


def make_handler(api: HelpDeskApi):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # keep the terminal quiet
            pass

        def send(self, code: int, body: bytes, content_type: str):
            self.send_response(code)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, code: int, data):
            self.send(code, json.dumps(to_json(data)).encode("utf-8"), "application/json")

        def call(self, method: str, arg):
            try:
                self.send_json(200, getattr(api, method)(arg))
            except Exception as e:  # turn every service error into a message for the page
                code = next((c for t, c in ERRORS if isinstance(e, t)), 500)
                msg = f"Not built yet ({e})." if code == 501 else str(e) or "Something went wrong."
                self.send_json(code, {"error": msg})

        def do_GET(self):
            url = urlparse(self.path)
            if url.path in STATIC_FILES:
                name, ctype = STATIC_FILES[url.path]
                return self.send(200, (STATIC_DIR / name).read_bytes(), ctype)
            if url.path in GET_ROUTES:
                q = {k: v[0] for k, v in parse_qs(url.query).items()}
                return self.call(GET_ROUTES[url.path], q)
            self.send_json(404, {"error": "Page not found."})

        def do_POST(self):
            path = urlparse(self.path).path
            if path not in POST_ROUTES:
                return self.send_json(404, {"error": "Page not found."})
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self.send_json(400, {"error": "The request could not be read."})
            self.call(POST_ROUTES[path], body)

    return Handler


def start_server(port: int = 8000, api: HelpDeskApi | None = None) -> ThreadingHTTPServer:
    """Start on the first free port from `port` upward. Returns the running server."""
    handler = make_handler(api or HelpDeskApi())
    for p in range(port, port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", p), handler)
            break
        except OSError:
            continue
    else:
        raise OSError("No free port between 8000 and 8019.")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main() -> None:
    server = start_server()
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Campus Technology Help Desk is running at {url}")
    print("Your browser should open automatically. Press Ctrl+C here to stop.")
    webbrowser.open(url)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        server.shutdown()
        print("\nStopped.")

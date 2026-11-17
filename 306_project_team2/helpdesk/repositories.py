"""Loads and saves domain objects as JSON (NFR-03). No business rules here.
Each save writes a temporary file first, then renames it over the old one,
so a crash during a save cannot leave a half-written file."""
from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from helpdesk.models import (Assignment, Note, NoteType, Priority, Request, Role, Status,
                             StatusChange, User)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _write(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    os.replace(tmp, path)


class UserRepository:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.path = Path(data_dir) / "users.json"

    def all(self) -> list[User]:
        return [User(r["user_id"], r["name"], Role(r["role"])) for r in _read(self.path)]

    def get(self, user_id: str) -> User | None:
        return next((u for u in self.all() if u.user_id == user_id), None)


class RequestRepository:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.path = Path(data_dir) / "requests.json"

    @staticmethod
    def _from_dict(r: dict) -> Request:
        a = r.get("assignment")
        return Request(
            request_id=r["request_id"], title=r["title"], description=r["description"],
            location=r["location"], category=r["category"],
            requested_urgency=Priority(r["requested_urgency"]), priority=Priority(r["priority"]),
            status=Status(r["status"]), requester_id=r["requester_id"],
            created_at=r["created_at"], updated_at=r["updated_at"],
            assignment=Assignment(**a) if a else None,
            history=[StatusChange(Status(h["from_status"]) if h["from_status"] else None,
                                  Status(h["to_status"]), h["changed_by"], h["changed_at"])
                     for h in r.get("history", [])],
        )

    def all(self) -> list[Request]:
        return [self._from_dict(r) for r in _read(self.path)]

    def get(self, request_id: str) -> Request | None:
        return next((r for r in self.all() if r.request_id == request_id), None)

    def save(self, request: Request) -> None:
        """Insert or replace one request, then write the file."""
        rows = [r for r in _read(self.path) if r["request_id"] != request.request_id]
        rows.append(asdict(request))
        rows.sort(key=lambda r: r["request_id"])
        _write(self.path, rows)

    def next_id(self) -> str:
        nums = [int(r["request_id"].split("-")[1]) for r in _read(self.path)]
        return f"R-{(max(nums) + 1) if nums else 1:04d}"


class NoteRepository:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.path = Path(data_dir) / "notes.json"

    def for_request(self, request_id: str) -> list[Note]:
        return [Note(n["note_id"], n["request_id"], NoteType(n["type"]), n["text"],
                     n["author_id"], n["created_at"])
                for n in _read(self.path) if n["request_id"] == request_id]

    def add(self, note: Note) -> None:
        rows = _read(self.path)
        rows.append(asdict(note))
        _write(self.path, rows)

    def next_id(self) -> str:
        nums = [int(n["note_id"].split("-")[1]) for n in _read(self.path)]
        return f"N-{(max(nums) + 1) if nums else 1:04d}"

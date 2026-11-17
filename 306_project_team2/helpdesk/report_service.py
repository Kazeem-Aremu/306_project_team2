"""Activity summary counts (FR-08 / Story 3). Read-only."""
from __future__ import annotations

from collections import Counter

from helpdesk.models import CATEGORIES, CLOSED_STATUSES, OPEN_STATUSES, Priority, Request, Status


class ReportService:
    def __init__(self, requests: list[Request]):
        self.requests = requests

    def count_open_closed(self) -> dict[str, int]:
        """{'Open': n, 'Closed': n, 'Cancelled': n}. Resolved counts as closed
        (open question 2 for the instructor)."""
        return {
            "Open": sum(r.status in OPEN_STATUSES for r in self.requests),
            "Closed": sum(r.status in CLOSED_STATUSES for r in self.requests),
            "Cancelled": sum(r.status == Status.CANCELLED for r in self.requests),
        }

    def count_by_category(self) -> dict[str, int]:
        """Every category, in the fixed order, including those with zero requests."""
        counts = Counter(r.category for r in self.requests)
        return {c: counts.get(c, 0) for c in CATEGORIES}

    def count_by_priority(self) -> dict[str, int]:
        counts = Counter(r.priority for r in self.requests)
        return {p.value: counts.get(p, 0) for p in Priority}

    def count_by_technician(self) -> dict[str, int]:
        """Open requests per technician ID; open requests with no technician under 'Unassigned'."""
        counts: Counter[str] = Counter()
        for r in self.requests:
            if r.is_open():
                counts[r.assignment.technician_id if r.assignment else "Unassigned"] += 1
        return dict(sorted(counts.items(), key=lambda kv: (kv[0] != "Unassigned", kv[0])))

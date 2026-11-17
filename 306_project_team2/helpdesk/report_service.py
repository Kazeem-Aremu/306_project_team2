"""Activity summary counts (FR-08 / Story 3). Read-only."""
from __future__ import annotations

from helpdesk.models import Request


class ReportService:
    def __init__(self, requests: list[Request]):
        self.requests = requests

    def count_open_closed(self) -> dict[str, int]:
        """{'Open': n, 'Closed': n, 'Cancelled': n} using OPEN_STATUSES / CLOSED_STATUSES."""
        raise NotImplementedError("FR-08: open vs closed counts")

    def count_by_category(self) -> dict[str, int]:
        raise NotImplementedError("FR-08: counts by category")

    def count_by_priority(self) -> dict[str, int]:
        raise NotImplementedError("FR-08: counts by priority")

    def count_by_technician(self) -> dict[str, int]:
        """Open requests per technician; unassigned ones under 'Unassigned'."""
        raise NotImplementedError("FR-08: counts by technician")

"""Shared test setup: every test works on a fresh copy of the sample data,
so tests never change data/ and never depend on each other."""
import shutil
import tempfile
import unittest
from pathlib import Path

from helpdesk.repositories import DATA_DIR, NoteRepository, RequestRepository, UserRepository
from helpdesk.request_service import RequestService


class DataTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for f in DATA_DIR.glob("*.json"):
            shutil.copy(f, self.tmp / f.name)
        self.users = UserRepository(self.tmp)
        self.requests = RequestRepository(self.tmp)
        self.notes = NoteRepository(self.tmp)
        self.service = RequestService(self.requests, self.notes, self.users)
        self.requester = self.users.get("U-101")
        self.coordinator = self.users.get("C-01")
        self.tech = self.users.get("T-01")
        self.other_tech = self.users.get("T-02")

    def tearDown(self):
        shutil.rmtree(self.tmp)

"""NFR-01 / NFR-02: the browser interface serves the page and turns service errors into
clear messages. Runs the real local server on a free port."""
import json
import unittest
import urllib.error
import urllib.request

from helpdesk.web import HelpDeskApi, start_server
from tests.helpers import DataTestCase


class WebTest(DataTestCase):
    def setUp(self):
        super().setUp()
        self.server = start_server(8600, HelpDeskApi(self.service))
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        super().tearDown()

    def fetch(self, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as res:
                return res.status, res.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def test_page_is_served(self):
        code, body = self.fetch("/")
        self.assertEqual(code, 200)
        self.assertIn(b"Campus Tech Help Desk", body)

    def test_users_are_listed(self):
        code, body = self.fetch("/api/users?user=")
        self.assertEqual(code, 200)
        self.assertEqual(len(json.loads(body)), 7)

    def test_request_detail_shows_allowed_next_statuses(self):
        code, body = self.fetch("/api/request?user=C-01&id=R-0001")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["allowed_next"], ["Reviewed", "Cancelled"])

    def test_unknown_request_is_404(self):
        code, _ = self.fetch("/api/request?user=C-01&id=R-9999")
        self.assertEqual(code, 404)

    def test_incomplete_submit_returns_clear_message(self):
        code, body = self.fetch("/api/submit", {"user": "U-101", "title": "t"})
        self.assertEqual(code, 400)
        self.assertIn("Description is required", json.loads(body)["error"])

    def test_valid_submit_through_the_page(self):
        code, body = self.fetch("/api/submit", {"user": "U-101", "title": "Mouse broken",
                                                "description": "Left button dead.", "location": "Library 101",
                                                "category": "Hardware", "urgency": "Low"})
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["status"], "Submitted")

    def test_requester_cannot_open_someone_elses_request(self):
        code, _ = self.fetch("/api/request?user=U-101&id=R-0002")  # R-0002 belongs to U-102
        self.assertEqual(code, 403)

    def test_requester_cannot_open_summary(self):
        code, _ = self.fetch("/api/summary?user=U-101")
        self.assertEqual(code, 403)

    def test_bad_json_is_rejected(self):
        req = urllib.request.Request(self.base + "/api/note", data=b"{not json", method="POST")
        try:
            urllib.request.urlopen(req)
            self.fail("expected an error")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)


if __name__ == "__main__":
    unittest.main()

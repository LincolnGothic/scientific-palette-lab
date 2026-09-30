import base64
import http.client
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from palette_lab.app import Application, handler_for
from palette_lab.demo import seed_demo
from palette_lab.hosting import WebAccess
from palette_lab.store import Store


TEST_PASSWORD = "fictional-test-password-only"


class HostingTests(unittest.TestCase):
    def test_external_binding_requires_https_and_password(self):
        WebAccess().validate("127.0.0.1")
        for access in (WebAccess(), WebAccess("https://lab.example.test"),
                       WebAccess("http://lab.example.test", password=TEST_PASSWORD),
                       WebAccess("https://lab.example.test/path", password=TEST_PASSWORD)):
            with self.assertRaises(ValueError):
                access.validate("0.0.0.0")
        WebAccess("https://lab.example.test", password=TEST_PASSWORD).validate("0.0.0.0")

    def test_malformed_and_wrong_credentials_are_rejected(self):
        access = WebAccess(password=TEST_PASSWORD)
        for header in (None, "Basic !!!", "Bearer x", "Basic " + "x"*9000,
                       "Basic " + base64.b64encode(b"researcher:incorrect").decode()):
            self.assertFalse(access.authenticated(header))
        token = base64.b64encode(f"researcher:{TEST_PASSWORD}".encode()).decode()
        self.assertTrue(access.authenticated("Basic " + token))

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.directory.name))
        self.access = WebAccess("https://lab.example.test", password=TEST_PASSWORD)
        self.start_server()

    def start_server(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(Application(self.store), self.access))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def tearDown(self):
        self.stop_server()
        self.directory.cleanup()

    def request(self, path, auth=False, origin=None, method="GET", host="lab.example.test"):
        headers = {"Host": host}
        if auth:
            token = base64.b64encode(f"researcher:{TEST_PASSWORD}".encode()).decode()
            headers["Authorization"] = "Basic " + token
        if origin:
            headers["Origin"] = origin
        body = None
        if method == "POST":
            headers["Content-Type"] = "application/json"
            body = "{}"
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request(method, path, body, headers)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_all_workspace_resources_require_authentication(self):
        for path in ("/", "/app.js", "/api/state", "/api/export.json", "/assets/secret.png"):
            status, headers, _ = self.request(path)
            self.assertEqual(status, 401, path)
            self.assertIn("Basic", headers["WWW-Authenticate"])
        self.assertEqual(self.request("/api/import", method="POST")[0], 401)
        self.assertEqual(self.request("/", auth=True)[0], 200)
        self.assertEqual(self.request("/api/state", auth=True)[0], 200)

    def test_foreign_hosts_and_origins_are_rejected(self):
        self.assertEqual(self.request("/api/state", auth=True, host="attacker.test")[0], 403)
        self.assertEqual(self.request("/api/import", auth=True, method="POST", origin="https://attacker.test")[0], 403)
        self.assertEqual(self.request("/api/state", auth=True, origin="https://lab.example.test")[0], 200)

    def test_health_check_exposes_no_corpus_details(self):
        status, _, body = self.request("/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"status": "ok"})

    def test_corpus_survives_server_restart(self):
        seed_demo(self.store)
        before = json.loads(self.request("/api/state?dataset=demo", auth=True)[2])
        self.stop_server()
        self.store = Store(Path(self.directory.name))
        self.start_server()
        after = json.loads(self.request("/api/state?dataset=demo", auth=True)[2])
        self.assertEqual(after["overview"]["reviewed"], before["overview"]["reviewed"])
        self.assertGreater(after["overview"]["reviewed"], 0)
        self.assertEqual({p["id"] for p in after["panels"]}, {p["id"] for p in before["panels"]})

import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


class StartupTests(unittest.TestCase):
    def command(self, directory, port):
        return [sys.executable, "-m", "palette_lab", "--data-dir", directory,
                "serve", "--port", str(port)]

    def test_occupied_port_reports_recovery_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory, socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            result = subprocess.run(self.command(directory, port), cwd=PROJECT,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 1)
            self.assertIn(f"Port {port} is already in use", result.stderr)
            self.assertIn(f"http://127.0.0.1:{port}", result.stderr)
            self.assertIn("bash run.sh serve --port", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            # The occupied service remains available; startup must not terminate it.
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                pass

    def test_server_starts_and_serves_on_available_port(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, PYTHONUNBUFFERED="1")
            process = subprocess.Popen(self.command(directory, 0), cwd=PROJECT, env=env,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                # A port of zero lets the OS reserve an available port without a bind race.
                deadline = time.monotonic() + 10
                import select
                self.assertTrue(select.select([process.stdout], [], [],
                                              max(0, deadline-time.monotonic()))[0],
                                "Server did not announce its URL")
                first_line = process.stdout.readline().strip()
                self.assertTrue(first_line.startswith("Scientific Palette Lab → http://127.0.0.1:"), first_line)
                url = first_line.split(" → ", 1)[1]
                with urllib.request.urlopen(url, timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn(b"Scientific Palette Lab", response.read())
            finally:
                process.terminate()
                try:
                    process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate(timeout=5)

import os
import errno
import io
from contextlib import redirect_stderr
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from unittest.mock import Mock, patch
from pathlib import Path

from support import running_server, server_environment


PROJECT = Path(__file__).resolve().parents[1]


class DiagnosticTests(unittest.TestCase):
    def invoke(self, error):
        from palette_lab.__main__ import main
        directory = tempfile.TemporaryDirectory(dir=os.environ.get("RUNNER_TEMP"))
        self.addCleanup(directory.cleanup)
        output = io.StringIO()
        with patch("sys.argv", ["palette_lab", "--data-dir", directory.name,
                                "serve", "--host", "127.0.0.1", "--port", "8765"]), \
                patch("palette_lab.__main__.serve", side_effect=error), redirect_stderr(output):
            with self.assertRaises(SystemExit) as caught:
                main()
        self.assertEqual(caught.exception.code, 1)
        self.assertNotIn("Traceback", output.getvalue())
        return output.getvalue()

    def test_recognized_bind_errors_have_specific_diagnostics(self):
        cases = [(errno.EADDRINUSE, None, "already in use", "python -m palette_lab"),
                 (errno.EACCES, None, "access denied", "permitted port"),
                 (errno.EPERM, None, "access denied", "permissions"),
                 (errno.EADDRNOTAVAIL, None, "address unavailable", "present on this machine"),
                 (None, 10048, "already in use", "bash run.sh serve --port"),
                 (None, 10013, "access denied", "does not identify the cause"),
                 (None, 10049, "address unavailable", "present on this machine")]
        for code, winerror, category, recovery in cases:
            with self.subTest(errno=code, winerror=winerror):
                error = OSError(code, "fixture bind failure")
                if winerror is not None:
                    error.winerror = winerror
                output = self.invoke(error)
                self.assertIn(category, output)
                self.assertIn(recovery, output)
                self.assertIn(str(error), output)
                self.assertIn(str(winerror if winerror is not None else code), output)
                if category != "already in use":
                    self.assertIn("127.0.0.1:8765", output)

    def test_unknown_os_errors_propagate_unchanged(self):
        from palette_lab.__main__ import main
        directory = tempfile.TemporaryDirectory(dir=os.environ.get("RUNNER_TEMP"))
        self.addCleanup(directory.cleanup)
        for code, winerror in ((errno.EIO, None), (None, 10038)):
            error = OSError(code, "unexpected fixture failure")
            if winerror is not None:
                error.winerror = winerror
            with self.subTest(errno=code, winerror=winerror), \
                    patch("sys.argv", ["palette_lab", "--data-dir", directory.name, "serve"]), \
                    patch("palette_lab.__main__.serve", side_effect=error):
                with self.assertRaises(OSError) as caught:
                    main()
                self.assertIs(caught.exception, error)


class ServerSupportTests(unittest.TestCase):
    def test_failed_startups_are_bounded_diagnostic_and_reaped(self):
        import support
        actual_popen = subprocess.Popen
        state_failure = (
            "from http.server import HTTPServer,BaseHTTPRequestHandler\n"
            "class Handler(BaseHTTPRequestHandler):\n"
            " def do_GET(self):\n"
            "  self.send_response(200 if self.path == '/health' else 503); self.end_headers(); self.wfile.write(b'{\"status\":\"ok\"}')\n"
            "server=HTTPServer(('127.0.0.1',0),Handler)\n"
            "print('Scientific Palette Lab → http://127.0.0.1:'+str(server.server_port),flush=True)\n"
            "server.serve_forever()\n")
        for name, code, expected in (
                ("early-exit", "import sys; print('child failure', file=sys.stderr); sys.exit(7)", "returncode=7"),
                ("no-announcement", "print('unrelated output')", "returncode=0"),
                ("timeout", "import time; print('Scientific Palette Lab → http://127.0.0.1:1234', end='', flush=True); time.sleep(60)", "deadline"),
                ("silent-timeout", "import time; time.sleep(60)", "deadline"),
                ("health-timeout", "import socket,time; s=socket.socket(); s.bind(('127.0.0.1',0)); print('Scientific Palette Lab → http://127.0.0.1:'+str(s.getsockname()[1]),flush=True); time.sleep(60)", "last HTTP error=URLError"),
                ("state-failure", state_failure, "last HTTP error=<HTTPError 503")):
            with self.subTest(case=name):
                directory = tempfile.TemporaryDirectory(dir=os.environ.get("RUNNER_TEMP"))
                self.addCleanup(directory.cleanup)
                children = []
                handles = []
                def launch(*args, **kwargs):
                    process = actual_popen(*args, **kwargs)
                    children.append(process)
                    handles.extend((kwargs["stdout"], kwargs["stderr"]))
                    return process
                with patch("support.subprocess.Popen", side_effect=launch):
                    start = time.monotonic()
                    with self.assertRaises(AssertionError) as caught:
                        with support.running_server([sys.executable, "-X", "utf8", "-u", "-c", code],
                                                    PROJECT, directory.name, support.server_environment(),
                                                    startup_timeout=1):
                            self.fail("An incomplete startup must not yield")
                self.assertLess(time.monotonic() - start, 12)
                self.assertIn(expected, str(caught.exception))
                self.assertIn(directory.name, str(caught.exception))
                self.assertIn("stdout", str(caught.exception))
                self.assertIn("stderr", str(caught.exception))
                self.assertIsNotNone(children[0].poll())
                self.assertTrue(all(handle.closed for handle in handles))
                if name == "early-exit":
                    self.assertIn("child failure", str(caught.exception))

    def test_server_environment_clears_inherited_hosting_settings(self):
        from support import server_environment
        with patch.dict(os.environ, {"PORT": "invalid", "PALETTE_HOST": "0.0.0.0",
                                     "PALETTE_WEB_PASSWORD": "fixture", "RENDER_EXTERNAL_URL": "https://example.test"}):
            env = server_environment()
        self.assertFalse(any(key.upper() == "PORT" or key.upper().startswith("PALETTE_")
                             or key.upper() == "RENDER_EXTERNAL_URL" for key in env))
        self.assertEqual(env["PYTHONUTF8"], "1")
        self.assertEqual(env["PYTHONUNBUFFERED"], "1")

    def test_stop_process_kills_after_timeout_and_reports_failure_to_reap(self):
        from support import stop_process
        process = Mock()
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired("fixture", 5), 0]
        stop_process(process)
        process.terminate.assert_called_once_with()
        process.kill.assert_called_once_with()
        self.assertEqual(process.wait.call_args_list, [unittest.mock.call(timeout=5)] * 2)
        process.wait.side_effect = subprocess.TimeoutExpired("fixture", 5)
        with self.assertRaisesRegex(AssertionError, "reap"):
            stop_process(process)


class StartupTests(unittest.TestCase):
    def command(self, directory, port):
        return [sys.executable, "-B", "-X", "utf8", "-u", "-m", "palette_lab", "--data-dir", directory,
                "serve", "--host", "127.0.0.1", "--port", str(port)]

    def test_occupied_port_reports_recovery_without_traceback(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("RUNNER_TEMP")) as directory, socket.socket() as listener:
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            result = subprocess.run(self.command(directory, port), cwd=PROJECT,
                                    env=server_environment(), capture_output=True,
                                    text=True, encoding="utf-8", timeout=10)
            self.assertEqual(result.returncode, 1)
            if os.name == "nt" and "winerror=10013" in result.stderr:
                self.assertIn("access denied", result.stderr)
                self.assertIn(f"127.0.0.1:{port}", result.stderr)
                self.assertIn("permitted port", result.stderr)
                self.assertNotIn("already in use", result.stderr)
            else:
                self.assertIn(f"Port {port} is already in use", result.stderr)
                self.assertIn(f"http://127.0.0.1:{port}", result.stderr)
                self.assertIn("bash run.sh serve --port", result.stderr)
                self.assertIn("python -m palette_lab serve --port", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            # The occupied service remains available; startup must not terminate it.
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                pass

    def test_server_starts_and_serves_on_available_port(self):
        actual_popen = subprocess.Popen
        children, handles = [], []
        def launch(*args, **kwargs):
            process = actual_popen(*args, **kwargs)
            children.append(process)
            handles.extend((kwargs["stdout"], kwargs["stderr"]))
            return process
        with tempfile.TemporaryDirectory(dir=os.environ.get("RUNNER_TEMP")) as directory:
            with patch("support.subprocess.Popen", side_effect=launch):
                with running_server(self.command(directory, 0), PROJECT, directory, server_environment()) as (url, diagnostics):
                    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                    with opener.open(url, timeout=5) as response:
                        self.assertEqual(response.status, 200, diagnostics())
                        self.assertIn(b"Scientific Palette Lab", response.read())
            self.assertIsNotNone(children[0].poll())
            self.assertTrue(all(handle.closed for handle in handles))

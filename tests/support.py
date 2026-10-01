"""Portable, bounded server ownership for subprocess and HTTP tests."""

from contextlib import contextmanager
from http.client import HTTPException
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
from urllib.error import HTTPError
import urllib.request


def server_environment():
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper() != "PORT"
        and not key.upper().startswith("PALETTE_")
        and key.upper() != "RENDER_EXTERNAL_URL"
    }
    env.update(PYTHONUNBUFFERED="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    return env


def stop_process(process):
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired as exc:
            raise AssertionError(f"Failed to reap server process pid={process.pid}") from exc


def _tail(path):
    with path.open("rb") as log:
        log.seek(0, 2)
        log.seek(max(0, log.tell() - 65536))
        return log.read(65536).decode("utf-8", errors="replace")


def diagnostics(process, stdout_path, stderr_path, deadline, directory, url=None, error=None):
    return (
        f"pid={process.pid}, returncode={process.poll()}, deadline={deadline:.3f}, "
        f"data directory={directory}, last URL={url}, last HTTP error={error}\n"
        f"stdout:\n{_tail(stdout_path)}\nstderr:\n{_tail(stderr_path)}"
    )


def wait_for_url(process, stdout_path, stderr_path, deadline):
    while True:
        match = re.search(
            r"^Scientific Palette Lab → (http://127\.0\.0\.1:(\d+))\r?\n",
            _tail(stdout_path),
            re.MULTILINE,
        )
        if match and 0 < int(match.group(2)) <= 65535:
            return match.group(1)
        if process.poll() is not None or time.monotonic() >= deadline:
            raise AssertionError(
                diagnostics(process, stdout_path, stderr_path, deadline, stdout_path.parent)
            )
        time.sleep(0.05)


@contextmanager
def running_server(command, cwd, directory, env, startup_timeout=30):
    """Yield (loopback URL, callable diagnostics); always stop and reap the child."""
    directory = Path(directory)
    stdout_path, stderr_path = directory / "server.stdout.log", directory / "server.stderr.log"
    deadline = time.monotonic() + startup_timeout
    url, last_error = None, None
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stdout, stderr=stderr)

        def describe():
            return diagnostics(
                process, stdout_path, stderr_path, deadline, directory, url, last_error
            )

        try:
            url = wait_for_url(process, stdout_path, stderr_path, deadline)
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            while True:
                remaining = deadline - time.monotonic()
                if process.poll() is not None or remaining <= 0:
                    raise AssertionError(describe())
                try:
                    with opener.open(url + "/health", timeout=min(1, remaining)) as response:
                        if response.status == 200 and json.load(response) == {"status": "ok"}:
                            break
                        last_error = "Unexpected health response"
                except (OSError, ValueError, HTTPException) as exc:
                    last_error = repr(exc)
                    if isinstance(exc, HTTPError):
                        exc.close()
                time.sleep(min(0.05, max(0, deadline - time.monotonic())))
            try:
                with opener.open(url + "/api/state", timeout=2) as response:
                    if response.status != 200 or not isinstance(json.load(response), dict):
                        raise AssertionError(describe())
            except (OSError, ValueError, HTTPException) as exc:
                last_error = repr(exc)
                if isinstance(exc, HTTPError):
                    exc.close()
                raise AssertionError(describe()) from exc
            yield url, describe
        finally:
            stop_process(process)


def stop_http_server(server, thread):
    """Bound shutdown and join; a never-started serve loop needs only close."""
    try:
        if thread.ident is not None and thread.is_alive():
            shutdown = threading.Thread(target=server.shutdown, daemon=True)
            shutdown.start()
            shutdown.join(timeout=5)
            if shutdown.is_alive():
                raise AssertionError("HTTP shutdown thread did not terminate within 5 seconds")
    finally:
        server.server_close()
        if thread.ident is not None:
            thread.join(timeout=5)
            if thread.is_alive():
                raise AssertionError("HTTP serve thread did not terminate within 5 seconds")

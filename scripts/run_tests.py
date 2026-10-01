"""Offline unittest worker and bounded, process-owned watchdog."""

import argparse
import importlib.metadata
import importlib.resources
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import uuid

PROJECT = Path(__file__).resolve().parents[1]
LOG_LIMIT = 65536


def write_report(path, report):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def tail(path):
    with Path(path).open("rb") as stream:
        stream.seek(0, 2)
        stream.seek(max(0, stream.tell() - LOG_LIMIT))
        return stream.read(LOG_LIMIT).decode("utf-8", errors="replace")


def clean_environment():
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper() not in ("PYTHONPATH", "PYTHONHOME", "PORT", "RENDER_EXTERNAL_URL")
        and not key.upper().startswith("PALETTE_")
    }
    env.update(PYTHONUTF8="1", PYTHONUNBUFFERED="1", PYTHONDONTWRITEBYTECODE="1")
    return env


def environment_metadata():
    versions = {}
    for name in ("numpy", "Pillow", "scientific-palette-lab"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    commands = {}
    for name, command in (
        ("pip_freeze", [sys.executable, "-m", "pip", "freeze"]),
        ("node", ["node", "--version"]),
        ("ruff", ["ruff", "--version"]),
    ):
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            commands[name] = {
                "returncode": result.returncode,
                "stdout": result.stdout[-LOG_LIMIT:],
                "stderr": result.stderr[-LOG_LIMIT:],
            }
        except (OSError, subprocess.TimeoutExpired) as exc:
            commands[name] = {"status": "unavailable", "reason": str(exc)}
    return {
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "executable": sys.executable,
        "versions": versions,
        "tools": commands,
        "tested_commit_sha": os.environ.get("CI_COMMIT_SHA"),
        "commit_kind": "tested SHA (may be a PR merge-test commit)",
        "runner": {
            key: os.environ.get(key)
            for key in ("RUNNER_OS", "RUNNER_ARCH", "ImageOS", "ImageVersion")
        },
    }


def run_worker(report_path, tests_directory=None):
    report = {"status": "running", "environment": environment_metadata(), "remote_attempts": []}
    started = time.monotonic()
    write_report(report_path, report)

    def prohibit_remote(_self, url, *args, **kwargs):
        report["remote_attempts"].append(str(url))
        write_report(report_path, report)
        raise AssertionError(f"Offline suite prohibited Remote.get: {url}")

    class ReportingResult(unittest.TextTestResult):
        def stopTest(self, test):
            super().stopTest(test)
            report.update(
                testsRun=self.testsRun,
                failures=len(self.failures),
                errors=len(self.errors),
                skips=len(self.skipped),
                duration=time.monotonic() - started,
            )
            write_report(report_path, report)

    try:
        if not os.environ.get("PALETTE_TEST_CWD"):
            sys.path.insert(0, str(PROJECT))
        import palette_lab

        report["package_origin"] = str(Path(palette_lab.__file__).resolve())
        if os.environ.get("PALETTE_TEST_CWD") and (
            not Path(palette_lab.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
            or Path(palette_lab.__file__).resolve().is_relative_to(PROJECT)
        ):
            raise AssertionError("Installed worker imported a package outside its runtime venv")
        from palette_lab.corpus import Remote

        # Discovery adds tests/, never the source package root in installed mode.
        with patch.object(Remote, "get", prohibit_remote):
            suite = unittest.TestLoader().discover(str(tests_directory or PROJECT / "tests"))
            report["discovered"] = suite.countTestCases()
            write_report(report_path, report)
            if "test_exports" in sys.modules:
                sys.modules["test_exports"].APP_JS = Path(
                    str(importlib.resources.files("palette_lab").joinpath("web", "app.js"))
                )
                report["export_asset"] = str(sys.modules["test_exports"].APP_JS)
            result = unittest.TextTestRunner(verbosity=2, resultclass=ReportingResult).run(suite)
        successful = (
            result.wasSuccessful() and result.testsRun > 0 and not report["remote_attempts"]
        )
        report.update(
            status="passed" if successful else "failed",
            testsRun=result.testsRun,
            failures=len(result.failures),
            errors=len(result.errors),
            skips=len(result.skipped),
            duration=time.monotonic() - started,
        )
    except Exception as exc:
        report.update(status="failed", error=repr(exc), duration=time.monotonic() - started)
        successful = False
    write_report(report_path, report)
    return 0 if successful else 1


def stop_worker(process):
    if os.name == "nt":
        # This PID belongs to this watchdog; /T includes its owned descendants.
        try:
            result = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            diagnostic = {"returncode": result.returncode, "stderr": result.stderr[-LOG_LIMIT:]}
        except (OSError, subprocess.TimeoutExpired) as exc:
            diagnostic = {"error": str(exc)}
        if process.poll() is None:
            process.kill()
    else:
        diagnostic = {"process_group": process.pid}
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        # Descendants may outlive the worker; kill the owned group even if it exited.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=5)
    return diagnostic


def watchdog(command, timeout, report_path, worker_report, cwd, env):
    report_path, worker_report = Path(report_path), Path(worker_report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path = report_path.with_suffix(".stdout.log")
    stderr_path = report_path.with_suffix(".stderr.log")
    report = {
        "status": "unfinished",
        "environment": environment_metadata(),
        "testsRun": None,
        "failures": None,
        "errors": None,
        "skips": None,
        "timeout_seconds": timeout,
        "worker_report": str(worker_report),
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
    }
    write_report(report_path, report)
    started = time.monotonic()
    try:
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=stdout,
                stderr=stderr,
                start_new_session=os.name != "nt",
            )
            report["worker_pid"] = process.pid
            timed_out = False
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                report["termination"] = stop_worker(process)
            report["returncode"] = process.returncode
        if worker_report.exists():
            try:
                report.update(json.loads(worker_report.read_text(encoding="utf-8")))
            except (ValueError, OSError) as exc:
                report["worker_report_error"] = str(exc)
        report["status"] = (
            "timeout"
            if timed_out
            else "passed"
            if process.returncode == 0
            and report.get("status") == "passed"
            and report.get("testsRun", 0)
            and not report.get("remote_attempts")
            else "failed"
        )
        report["unfinished"] = timed_out or report.get("testsRun") is None
    except Exception as exc:
        report.update(status="failed", error=repr(exc), unfinished=True)
    report["watchdog_duration"] = time.monotonic() - started
    for name, path in (("stdout_tail", stdout_path), ("stderr_tail", stderr_path)):
        report[name] = tail(path) if path.exists() else ""
    write_report(report_path, report)
    print(report["stdout_tail"])
    print(report["stderr_tail"], file=sys.stderr)
    return 0 if report["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.worker:
        return run_worker(args.report)
    report_path = args.report.resolve()
    worker_report = report_path.with_name(
        report_path.stem + ".worker-" + uuid.uuid4().hex + ".json"
    )
    installed_cwd = os.environ.get("PALETTE_TEST_CWD")
    env = clean_environment()
    if installed_cwd:
        env["PALETTE_TEST_CWD"] = installed_cwd
    command = [sys.executable, "-B"]
    if installed_cwd:
        command.append("-I")
    command += [str(Path(__file__).resolve()), "--worker", "--report", str(worker_report)]
    return watchdog(
        command, args.timeout, report_path, worker_report, installed_cwd or PROJECT, env
    )


if __name__ == "__main__":
    sys.exit(main())

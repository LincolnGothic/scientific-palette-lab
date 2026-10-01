"""Installed resources, distribution metadata, existing schema and watchdog contracts."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.metadata
import importlib.resources
import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import Mock
from types import ModuleType, SimpleNamespace

import palette_lab
from palette_lab.store import Store

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "palette_test_watchdog", PROJECT / "scripts/run_tests.py"
)
watchdog_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watchdog_module)
hosting_spec = importlib.util.spec_from_file_location(
    "palette_test_hosting", PROJECT / "scripts/check_hosting.py"
)
hosting_module = importlib.util.module_from_spec(hosting_spec)
# Docker ownership tests exercise no YAML parsing; base tests need no dev extras.
with patch.dict(sys.modules, {"yaml": ModuleType("yaml"), "run_tests": watchdog_module}):
    hosting_spec.loader.exec_module(hosting_module)


class InstalledDeadlineTests(unittest.TestCase):
    def test_installed_call_allows_watchdog_to_finish_owned_cleanup(self):
        # Other distribution phases are mocked; exercise the actual installed call
        # and watchdog with a virtual clock/owned child, without dev dependencies.
        requirements = ModuleType("packaging.requirements")
        requirements.Requirement = Mock()
        spec = importlib.util.spec_from_file_location(
            "palette_test_distribution", PROJECT / "scripts/verify_distribution.py"
        )
        distribution = importlib.util.module_from_spec(spec)
        with patch.dict(
            sys.modules,
            {
                "packaging": ModuleType("packaging"),
                "packaging.requirements": requirements,
                "run_tests": watchdog_module,
            },
        ):
            spec.loader.exec_module(distribution)
        directory = tempfile.TemporaryDirectory(dir=os.environ.get("RUNNER_TEMP"))
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        runtime = root / "runtime"
        runtime.mkdir()
        package = runtime / "venv/Lib/site-packages/palette_lab/__init__.py"
        clock, events = [0.0], []
        owned = {"worker_alive": True, "descendant_alive": True, "cleaned": False}
        process = Mock(pid=424242, returncode=None)
        outer_deadline = [None]

        class OuterDeadlineExpired(BaseException):
            pass

        def metadata():
            clock[0] += 30
            events.append(["metadata_finished", clock[0]])
            return {}

        def wait(timeout):
            if outer_deadline[0] is not None and clock[0] + timeout >= outer_deadline[0]:
                clock[0] = outer_deadline[0]
                events.append(["outer_killed_watchdog", clock[0]])
                raise OuterDeadlineExpired()
            clock[0] += timeout
            events.append(["worker_timeout", clock[0]])
            raise subprocess.TimeoutExpired("owned-worker", timeout)

        def cleanup(child):
            self.assertIs(child, process)
            clock[0] += 15
            owned.update(worker_alive=False, descendant_alive=False, cleaned=True)
            process.returncode = -9
            events.append(["owned_tree_cleanup_finished", clock[0]])
            return {"owned_pid": child.pid}

        process.wait.side_effect = wait

        def run(arguments, **kwargs):
            if len(arguments) > 2 and Path(arguments[2]).name == "run_tests.py":
                budget = kwargs.get("timeout")
                outer_deadline[0] = budget
                suite_report = Path(arguments[arguments.index("--report") + 1])
                worker_report = root / "partial-worker.json"
                worker_report.write_text(
                    json.dumps({"status": "running", "testsRun": 2}), encoding="utf-8"
                )
                try:
                    with (
                        patch.object(watchdog_module, "environment_metadata", side_effect=metadata),
                        patch.object(
                            watchdog_module.time, "monotonic", side_effect=lambda: clock[0]
                        ),
                        patch.object(watchdog_module.subprocess, "Popen", return_value=process),
                        patch.object(watchdog_module, "stop_worker", side_effect=cleanup),
                        redirect_stdout(io.StringIO()),
                        redirect_stderr(io.StringIO()),
                    ):
                        code = watchdog_module.watchdog(
                            ["owned-worker"],
                            float(arguments[arguments.index("--timeout") + 1]),
                            suite_report,
                            worker_report,
                            root,
                            {},
                        )
                except OuterDeadlineExpired:
                    raise subprocess.TimeoutExpired(arguments, budget) from None
                return subprocess.CompletedProcess(arguments, code, "partial watchdog report", "")
            stdout = ""
            if "-c" in arguments:
                code = arguments[arguments.index("-c") + 1]
                if "'package':" in code:
                    stdout = json.dumps({"package": str(package), "prefix": str(runtime / "venv")})
                elif "read_bytes().hex()" in code:
                    stdout = json.dumps(
                        {
                            name: (PROJECT / "palette_lab/web" / name).read_bytes().hex()
                            for name in distribution.ASSETS
                        }
                    )
            return subprocess.CompletedProcess(arguments, 0, stdout, "")

        opener = Mock()
        opener.open.side_effect = [
            io.StringIO(json.dumps({"overview": {"papers": 0}, "panels": []})),
            *(
                io.BytesIO((PROJECT / "palette_lab/web" / name).read_bytes())
                for name in distribution.ASSETS
            ),
        ]
        server = Mock()
        server.return_value.__enter__ = Mock(
            return_value=("http://127.0.0.1:1234", lambda: "fixture")
        )
        server.return_value.__exit__ = Mock(return_value=False)
        report_path = root / "distribution.json"
        with (
            patch.object(distribution, "environment_metadata", return_value={}),
            patch.object(
                distribution,
                "inspect_archives",
                return_value=(root / "fixture.whl", {"status": "passed"}, []),
            ),
            patch.object(distribution.tempfile, "mkdtemp", return_value=str(runtime)),
            patch.object(distribution.venv.EnvBuilder, "create"),
            patch.object(distribution.subprocess, "run", side_effect=run),
            patch("support.running_server", server),
            patch.object(distribution.urllib.request, "build_opener", return_value=opener),
        ):
            result = distribution.verify(root, report_path)
        evidence = {"outer_deadline": outer_deadline[0], "events": events, **owned}
        (root / "deadline-evidence.json").write_text(
            json.dumps(evidence, indent=2), encoding="utf-8"
        )
        self.assertEqual(result, 1)  # The controlled worker timeout must propagate.
        self.assertTrue(owned["cleaned"], evidence)
        self.assertFalse(owned["worker_alive"], evidence)
        self.assertFalse(owned["descendant_alive"], evidence)
        self.assertEqual(
            events,
            [
                ["metadata_finished", 30.0],
                ["worker_timeout", 210.0],
                ["owned_tree_cleanup_finished", 225.0],
            ],
        )
        suite_report = report_path.with_name("distribution.installed-tests.json")
        partial = json.loads(suite_report.read_text(encoding="utf-8"))
        self.assertEqual(partial["status"], "timeout")
        self.assertEqual(partial["testsRun"], 2)
        self.assertTrue(partial["unfinished"])


class PackageTests(unittest.TestCase):
    def test_demo_has_twelve_records_and_no_real_papers(self):
        from palette_lab.demo import seed_demo

        with tempfile.TemporaryDirectory(dir=os.environ.get("RUNNER_TEMP")) as directory:
            store = Store(Path(directory))
            seed_demo(store)
            self.assertEqual(store.overview("demo")["papers"], 12)
            self.assertEqual(store.overview("real")["papers"], 0)

    def test_current_web_resources_are_nonempty(self):
        for name in ("index.html", "app.js", "style.css"):
            with self.subTest(asset=name):
                self.assertTrue(
                    importlib.resources.files("palette_lab").joinpath("web", name).read_bytes()
                )

    def test_installed_version_and_console_entry_point(self):
        self.assertEqual(palette_lab.__version__, "0.1.0")
        self.assertEqual(
            importlib.metadata.version("scientific-palette-lab"), palette_lab.__version__
        )
        entries = list(importlib.metadata.distribution("scientific-palette-lab").entry_points)
        console = [
            entry
            for entry in entries
            if entry.group == "console_scripts" and entry.name == "palette-lab"
        ]
        self.assertEqual(len(console), 1)
        self.assertEqual(console[0].value, "palette_lab.__main__:main")
        from palette_lab.__main__ import main

        self.assertIs(console[0].load(), main)

    def test_fresh_schema_columns_wal_and_foreign_keys(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("RUNNER_TEMP")) as directory:
            store = Store(Path(directory))
            expected = {
                "papers": [
                    "id",
                    "journal",
                    "year",
                    "title",
                    "doi",
                    "pmcid",
                    "source_url",
                    "license",
                    "version",
                    "eligibility",
                    "is_demo",
                    "metadata",
                    "created_at",
                ],
                "figures": [
                    "id",
                    "paper_id",
                    "source_key",
                    "label",
                    "caption",
                    "asset_path",
                    "source_url",
                    "sha256",
                    "width",
                    "height",
                ],
                "panels": [
                    "id",
                    "figure_id",
                    "label",
                    "bbox",
                    "extraction_bbox",
                    "kind",
                    "palette_type",
                    "colors",
                    "extraction",
                    "reviewed",
                    "active",
                    "notes",
                    "revision",
                    "updated_at",
                ],
                "reviews": ["id", "panel_id", "snapshot", "created_at"],
                "runs": ["id", "config", "report", "created_at"],
            }
            with store.connect() as db:
                tables = {
                    row[0]
                    for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
                }
                self.assertEqual(tables, set(expected))
                for table, columns in expected.items():
                    self.assertEqual(
                        [row[1] for row in db.execute(f"PRAGMA table_info({table})")], columns
                    )
                self.assertEqual(db.execute("PRAGMA journal_mode").fetchone()[0], "wal")
                self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
                self.assertEqual(
                    [
                        (row[2], row[3], row[4])
                        for row in db.execute("PRAGMA foreign_key_list(figures)")
                    ],
                    [("papers", "paper_id", "id")],
                )
                self.assertEqual(
                    [
                        (row[2], row[3], row[4])
                        for row in db.execute("PRAGMA foreign_key_list(panels)")
                    ],
                    [("figures", "figure_id", "id")],
                )
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute("INSERT INTO figures(id,paper_id) VALUES('orphan','absent')")


class WatchdogTests(unittest.TestCase):
    def test_discovery_is_independent_of_the_default_loader_root(self):
        with patch.object(unittest.defaultTestLoader, "_top_level_dir", str(PROJECT / "tests")):
            code, report = self.worker_case(
                "import unittest\nclass FreshRoot(unittest.TestCase):\n def test_pass(self): pass\n",
                "test_fresh_root_fixture.py",
            )
            self.assertEqual(unittest.defaultTestLoader._top_level_dir, str(PROJECT / "tests"))
        self.assertEqual(code, 0, report)
        self.assertEqual(report["discovered"], 1)
        self.assertEqual(report["testsRun"], 1)
        self.assertEqual(report["status"], "passed")

    def test_worker_asset_substitution_reaches_actual_harness_command(self):
        import test_exports

        with (
            patch.object(test_exports, "APP_JS", test_exports.APP_JS),
            patch.object(importlib.resources, "files", return_value=Path("installed-sentinel")),
        ):
            code, report = self.worker_case(
                "import unittest,test_exports,importlib.resources\n"
                "from unittest.mock import patch\n"
                "from pathlib import Path\n"
                "class Consumer(unittest.TestCase):\n"
                " def test_asset(self):\n"
                "  case=test_exports.ExportTests(); case.node='node'\n"
                "  with patch('test_exports.subprocess.run') as call: case.run_harness([])\n"
                "  expected=Path(str(importlib.resources.files('palette_lab').joinpath('web','app.js')))\n"
                "  self.assertEqual(Path(call.call_args.args[0][2]),expected)\n",
                "test_asset_consumer_fixture.py",
            )
        self.assertEqual(code, 0, report)
        self.assertEqual(report["testsRun"], 1)
        self.assertEqual(report["export_asset"], str(Path("installed-sentinel/web/app.js")))

    def worker_case(self, body, filename="test_case.py"):
        directory = tempfile.TemporaryDirectory(dir=os.environ.get("RUNNER_TEMP"))
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        if body:
            (root / filename).write_text(body, encoding="utf-8")
        report = root / "result.json"
        # Each synthetic discovery owns its module name, avoiding unittest's imported-path ambiguity.
        sys.modules.pop(Path(filename).stem, None)
        with (
            patch.object(watchdog_module, "environment_metadata", return_value={}),
            redirect_stderr(io.StringIO()),
            redirect_stdout(io.StringIO()),
        ):
            result = watchdog_module.run_worker(report, root)
        return result, json.loads(report.read_text(encoding="utf-8"))

    def test_no_tests_fail_with_truthful_zero_counts(self):
        code, report = self.worker_case("")
        self.assertEqual(code, 1)
        self.assertEqual(report["discovered"], 0)
        self.assertEqual(report["testsRun"], 0)
        self.assertEqual(report["status"], "failed")

    def test_failures_errors_and_skips_are_dynamic(self):
        code, report = self.worker_case(
            "import unittest\nclass Counts(unittest.TestCase):\n def test_fail(self): self.fail('fixture')\n def test_error(self): raise ValueError('fixture')\n @unittest.skip('fixture')\n def test_skip(self): pass\n",
            "test_counts_fixture.py",
        )
        self.assertEqual(code, 1)
        self.assertEqual(
            [report[key] for key in ("testsRun", "failures", "errors", "skips")], [3, 1, 1, 1]
        )

    def test_swallowed_real_remote_attempt_still_fails(self):
        code, report = self.worker_case(
            "import unittest\nfrom palette_lab.corpus import Remote\nclass Offline(unittest.TestCase):\n def test_swallow(self):\n  try: Remote().get('https://example.test/forbidden')\n  except AssertionError: pass\n",
            "test_remote_fixture.py",
        )
        self.assertEqual(code, 1)
        self.assertEqual(report["failures"], 0)
        self.assertEqual(report["remote_attempts"], ["https://example.test/forbidden"])

    def test_fake_remote_is_allowed(self):
        code, report = self.worker_case(
            "import unittest\nclass FakeRemote:\n def get(self,url): return b'offline'\nclass Offline(unittest.TestCase):\n def test_fixture(self): self.assertEqual(FakeRemote().get('fixture'),b'offline')\n",
            "test_fake_remote_fixture.py",
        )
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["remote_attempts"], [])

    def parent_case(self, code, timeout=10):
        directory = tempfile.TemporaryDirectory(dir=os.environ.get("RUNNER_TEMP"))
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        report, worker = root / "parent.json", root / "worker.json"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = watchdog_module.watchdog(
                [sys.executable, "-I", "-c", code, str(worker)],
                timeout,
                report,
                worker,
                root,
                watchdog_module.clean_environment(),
            )
        return result, json.loads(report.read_text(encoding="utf-8"))

    def test_early_exit_and_missing_report_are_unknown_counts(self):
        for code in (0, 7):
            with self.subTest(exit_code=code):
                result, report = self.parent_case(
                    f"import sys; print('early exit', file=sys.stderr); sys.exit({code})"
                )
                self.assertEqual(result, 1)
                self.assertEqual(report["returncode"], code)
                self.assertIsNone(report["testsRun"])
                self.assertTrue(report["unfinished"])
                self.assertIn("early exit", report["stderr_tail"])

    def test_timeout_preserves_partial_counts_and_bounds_logs(self):
        result, report = self.parent_case(
            "import sys,json,time; open(sys.argv[1],'w').write(json.dumps({'status':'running','testsRun':2,'failures':0,'errors':0,'skips':0})); print('x'*70000,flush=True); time.sleep(60)",
            timeout=1,
        )
        self.assertEqual(result, 1)
        self.assertEqual(report["status"], "timeout")
        self.assertEqual(report["testsRun"], 2)
        self.assertTrue(report["unfinished"])
        self.assertIsNotNone(report["returncode"])
        self.assertEqual(len(report["stdout_tail"].encode()), watchdog_module.LOG_LIMIT)
        self.assertLess(report["watchdog_duration"], 20)

    def test_parent_rejects_failed_worker_even_with_zero_exit(self):
        result, report = self.parent_case(
            "import sys,json; open(sys.argv[1],'w').write(json.dumps({'status':'failed','testsRun':1,'failures':1,'errors':0,'skips':0}))"
        )
        self.assertEqual(result, 1)
        self.assertEqual(report["status"], "failed")

    def test_parent_accepts_positive_successful_count(self):
        result, report = self.parent_case(
            "import sys,json; open(sys.argv[1],'w').write(json.dumps({'status':'passed','testsRun':4,'failures':0,'errors':0,'skips':1,'remote_attempts':[]}))"
        )
        self.assertEqual(result, 0)
        self.assertEqual(report["testsRun"], 4)

    def test_parent_rejects_zero_tests_even_with_passed_report(self):
        result, report = self.parent_case(
            "import sys,json; open(sys.argv[1],'w').write(json.dumps({'status':'passed','testsRun':0}))"
        )
        self.assertEqual(result, 1)
        self.assertEqual(report["status"], "failed")


class DockerOwnershipTests(unittest.TestCase):
    def launch_case(
        self, launch, stop_fails=False, kill_fails=False, image_fails=False, absent=False
    ):
        directory = tempfile.TemporaryDirectory(dir=os.environ.get("RUNNER_TEMP"))
        self.addCleanup(directory.cleanup)
        report_path = Path(directory.name) / "docker.json"
        report = {"docker": {"status": "unexecuted"}}
        calls = []
        name = "palette-ci-" + "a" * 32

        def run(command, **kwargs):
            calls.append((command, kwargs["timeout"]))
            if command[1] == "image":
                if image_fails:
                    return subprocess.CompletedProcess(command, 1, "", "image failure")
                return subprocess.CompletedProcess(command, 0, '[{"Id":"sha256:fixture"}]', "")
            if command[1] == "run":
                self.assertEqual(command[command.index("--name") + 1], name)
                if launch == "timeout":
                    raise subprocess.TimeoutExpired(command, kwargs["timeout"])
                return subprocess.CompletedProcess(
                    command, 1, "", "daemon created fixture then failed"
                )
            if command[1] == "logs":
                return subprocess.CompletedProcess(command, 0, "owned stdout", "owned stderr")
            if command[1] == "stop" and stop_fails:
                return subprocess.CompletedProcess(command, 1, "", "fixture stop failure")
            if command[1] == "kill" and kill_fails:
                return subprocess.CompletedProcess(command, 1, "", "fixture kill failure")
            if command[1:3] == ["container", "inspect"] and absent:
                return subprocess.CompletedProcess(command, 1, "[]", f"No such container: {name}")
            return subprocess.CompletedProcess(command, 0, "", "")

        with (
            patch.object(hosting_module.uuid, "uuid4", return_value=SimpleNamespace(hex="a" * 32)),
            patch.object(hosting_module.subprocess, "run", side_effect=run),
        ):
            hosting_module.smoke_docker("fixture-image", report, report_path)
        return name, calls, report["docker"]

    def test_launch_timeout_and_failure_still_log_and_stop_owned_name(self):
        for launch in ("timeout", "failure"):
            with self.subTest(launch=launch):
                name, calls, detail = self.launch_case(launch)
                self.assertEqual(detail["status"], "failed")
                self.assertEqual(
                    calls[-2:],
                    [(["docker", "logs", name], 10), (["docker", "stop", "--time", "5", name], 15)],
                )
                self.assertIn("owned stdout", Path(detail["logs"]).read_text())
                self.assertIn("owned stderr", Path(detail["logs"]).read_text())
                self.assertIn("Owned container stopped", detail["cleanup"])

    def test_launch_failure_force_stops_only_owned_name_after_stop_failure(self):
        name, calls, detail = self.launch_case("failure", stop_fails=True)
        self.assertEqual(calls[-1], (["docker", "kill", name], 10))
        self.assertIn("stop_error", detail)
        self.assertEqual(detail["cleanup"], "Owned container force-stopped")
        self.assertEqual(detail["status"], "failed")

    def test_launch_failure_preserves_cleanup_failure(self):
        name, calls, detail = self.launch_case("failure", stop_fails=True, kill_fails=True)
        self.assertEqual(
            calls[-2:],
            [(["docker", "kill", name], 10), (["docker", "container", "inspect", name], 10)],
        )
        self.assertIn("cleanup_error", detail)
        self.assertEqual(detail["status"], "failed")

    def test_uncertain_launch_with_confirmed_absence_does_not_claim_cleanup_failure(self):
        name, calls, detail = self.launch_case(
            "failure", stop_fails=True, kill_fails=True, absent=True
        )
        self.assertEqual(calls[-1], (["docker", "container", "inspect", name], 10))
        self.assertEqual(detail["cleanup"], "Owned container confirmed absent")
        self.assertNotIn("cleanup_error", detail)
        self.assertEqual(detail["status"], "failed")

    def test_prelaunch_image_failure_touches_no_container(self):
        _name, calls, detail = self.launch_case("failure", image_fails=True)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0][:3], ["docker", "image", "inspect"])
        self.assertEqual(detail["status"], "failed")


if __name__ == "__main__":
    unittest.main()

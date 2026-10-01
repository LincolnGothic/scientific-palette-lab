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
import sys
import tempfile
import unittest
from unittest.mock import patch

import palette_lab
from palette_lab.store import Store

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "palette_test_watchdog", PROJECT / "scripts/run_tests.py"
)
watchdog_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watchdog_module)


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


if __name__ == "__main__":
    unittest.main()

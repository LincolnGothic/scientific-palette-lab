# Task 4 — fix round 1

Status: DONE_WITH_CONCERNS. Both Important findings are addressed and targeted local checks pass. Hosted/native cleanup and real Docker remain unrun. No Git commits or D repository edits were made by this worker.

Read `task-4-review.md` in full after it became available. The controller explicitly authorized the narrow export-test edit. Changes are limited to three shipped staging files:

- `tests/test_exports.py`: `run_harness(..., source=None)` now resolves `APP_JS` at call time. Explicit mutation-fixture paths retain their existing behavior.
- `scripts/check_hosting.py`: marks launch attempted immediately before `docker run`; finally captures logs and performs bounded stop/kill using the pre-owned UUID name even when the run command times out or fails before returning its container ID. It does not touch a container on a prelaunch image-inspection failure. If stop/kill both fail, a bounded inspection of that same name distinguishes confirmed absence from an actual cleanup failure. Launch/log/stop/cleanup diagnostics are preserved; failures remain failed.
- `tests/test_package.py`: adds an actual worker-to-harness consumer regression and five mocked Docker ownership tests. A test-local `yaml` module stub is used only while importing the Docker smoke function; no YAML parsing is mocked in the static hosting job, and base-only test/runtime environments need no PyYAML or other dev extras.

## Red/green evidence

Before changing the affected implementations, added the consumer/ownership regressions and ran:

`D:/Codex_skill/codex-runtimes/pr01-source-audit/Scripts/python.exe F:/codex/Project Plan/pr01-implementation/run_retained_tests.py --source F:/codex/Project Plan/pr01-implementation/source --pattern test_package.py --report F:/codex/Project Plan/pr01-implementation/reports/task-4-fix-1-red.json`

Result: 18 tests, **five expected failures**, zero errors/skips. One failure demonstrates that production worker substitution records the sentinel asset while the actual harness command retains its import-time default. Four failure records (including timeout/failure subcases) demonstrate missing owned-name log/stop/kill handling. The prelaunch ownership case and prior baseline tests pass. All local test artifacts are retained.

After the minimal implementation fixes, the same focused retained command initially passed 18/18. After adding the reviewer-requested confirmed-absence case, final focused run passed **19/19**, zero failures/errors/skips in 10.407 seconds; evidence is `task-4-fix-1-green-final.json`. The absence case confirms that a failed launch remains failed without falsely claiming inability to clean up a container independently confirmed nonexistent.

Additional exact consumer capture in `task-4-fix-1-red-green-consumer-capture.json` reconstructs only the reviewed old default binding in memory (disk untouched), applies the identical installed APP_JS replacement, and captures the `subprocess.run` source argument:

- Reviewed binding: actual argument `F:/codex/Project Plan/pr01-implementation/source/palette_lab/web/app.js`, `uses_installed=false`.
- Corrected binding: actual argument inside the retained clean runtime venv's `Lib/site-packages/palette_lab/web/app.js`, `uses_installed=true`.

The permanent regression exercises the actual production `run_worker` discovery/substitution and invokes `ExportTests.run_harness`; its expected argument comes from the same substituted resource provider. It tests the consumer, not just the worker metadata.

## Installed acceptance with actual Node consumer capture

Reused the existing independently installed clean wheel runtime; no rebuild, new venv install, dependency download or package source change was needed. Executed its Python with `-I`, an external cwd, the production worker, and the existing `run_retained_tests.py` cleanup adaptations through `artifacts/task4-fix1-installed-consumer-audit.py`. The driver records harness subprocess arguments while delegating to the real subprocess implementation.

Command: runtime Python recorded in `task-4-fix-1-runtime.json`, followed by `-I F:/codex/Project Plan/pr01-implementation/artifacts/task4-fix1-installed-consumer-audit.py F:/codex/Project Plan/pr01-implementation/source F:/codex/Project Plan/pr01-implementation/reports/task-4-fix-1-installed.json`.

Result: **84/84** tests pass, zero failures/errors/skips, 27.014 seconds; production worker reports zero Remote.get attempts, package/asset origin within that runtime venv. Evidence:

- `task-4-fix-1-installed.json`: retained unittest counts/artifact root.
- `task-4-fix-1-installed.worker.json`: production worker environment/counts/offline guard.
- `task-4-fix-1-installed.stdout.log` / `.stderr.log`: full run logs.
- `task-4-fix-1-installed.consumer-capture.json`: **all four ordinary Node harness calls used the installed wheel's app.js**, `all_ordinary_calls_use_installed=true`. The five deliberate marker mutations consumed their explicit owned fixture files, preserving negative export coverage.

This proves the actual JS consumer path after the fix. The earlier 78-test report's installed-JS masking interpretation was incorrect despite valid package-origin/resource-byte checks. `task-4-report.md` now explicitly supersedes that interpretation while preserving the original evidence and its limits. Historical JSON/counts were not rewritten to imply a different run.

## Docker ownership checks

No Docker command or container ran locally; `subprocess.run` was mocked at the CLI boundary. The tests exercise real `docker_command` failure handling and finally cleanup. Exact asserted cleanup targets are the same pre-owned `palette-ci-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` name passed to the simulated run:

- Launch timeout and nonzero launch: `docker logs <owned-name>` timeout 10; `docker stop --time 5 <owned-name>` timeout 15. Both stdout/stderr logs are retained and launch status remains failed.
- Stop failure: `docker kill <owned-name>` timeout 10, stop diagnostic retained, force-stop recorded without touching another name.
- Stop plus kill failure: bounded `docker container inspect <owned-name>` timeout 10; unavailable cleanup remains a reported failure.
- Confirmed absence from that inspection: records owned container absent, retains original launch failure, does not fabricate a cleanup failure.
- Prelaunch image inspection failure: only image inspection occurs; no container operations.

## Other checks and limits

Ruff 0.13.3 lint and format checks of the three affected files pass (`All checks passed!`, `3 files already formatted`). The full installed suite includes all export tests and the new mock ownership cases in the base-only runtime. No unchanged broad build was repeated.

All artifacts were retained. Physical directory/file cleanup remains **unverified locally**. The installed audit uses the documented retained harness/production-worker adaptation, so the unchanged full-suite parent watchdog/native cleanup still require hosted execution. Real Docker, Linux/Windows matrix/minimum floors, CI Node 22 and native Bash remain hosted follow-through gates; no claim is made that those ran here.

Ready for scoped re-review of the three-file fix.

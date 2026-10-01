# Task 2 implementation report

Completed the approved portable startup, diagnostic, and test-isolation scope in the staging source. No commits, deletions, installations, production socket-policy changes, or application shutdown changes were performed.

## Files

- `palette_lab/__main__.py`: added `_startup_diagnostic` for symbolic EADDRINUSE, EACCES/EPERM, EADDRNOTAVAIL and Windows 10048/10013/10049. Preserves existing conflict recovery, adds `python -m palette_lab`, includes original error text and explicit errno/winerror, and propagates unknown OSError instances unchanged.
- `tests/support.py` (new): environment sanitizer; bounded file-log polling; newline-complete, validated loopback URL; no-proxy health readiness within the shared startup deadline; minimal state request; live bounded diagnostics; terminate/wait(5), kill/wait(5), and explicit failure to reap; bounded in-process shutdown/serve joins.
- `tests/test_cli.py`: mocked diagnostic/unknown-error cases, real exclusive test listener where supported, portable startup, environment sanitization, real early-exit/no-announcement/incomplete-line/silent-timeout/health-timeout/state-error children, child reaping and log-handle closure, deterministic forced-kill and reap-failure checks.
- `tests/test_hosting.py`: immediate directory/server cleanup registration; captured per-server cleanup across restart; bounded server shutdown; setup and thread-start failure checks; unauthenticated CSS/CSV, malformed HTTP credentials, foreign-host health, exact public health response, and authenticated traversal boundaries.
- `tests/test_pipeline.py`: immediate setup cleanup registration, and duplicate-import assertions for one paper, one figure/panel, stable figure ID, and one referenced asset.
- `tests/test_exports.py`: small reviewed offline PNG Store fixture for categorical, sequential, diverging, and role-based palettes, plus excluded/demo controls. Real HTTP JSON/CSV assertions cover response metadata, exact existing CSV columns, scope, sources, color sequence, roles, and counts. Existing browser-export tests unchanged.

Production algorithms, storage, demo, frontend, routing/authentication, and `app.py` are unchanged by this task.

## Reusable support interface

```python
with running_server(command, cwd, directory, server_environment(), startup_timeout=30) as (url, diagnostics):
    # url is validated http://127.0.0.1:<port>
    # diagnostics() reads current bounded log tails and process/HTTP state
    ...
```

`directory` must already exist and owns `server.stdout.log` and `server.stderr.log`. Callers supply an explicitly isolated data directory and command using loopback/port 0; Python commands use `-X utf8 -u` (and `-B` locally). Import the module from the repository's `tests` directory when using it in the installed smoke verifier. The helper owns and reaps its process and closes logs before returning from the context. Server termination demonstrates bounded ownership, not portable application-level graceful exit code 0.

## RED evidence

Before any production edit, `task-2-red-cli.json` recorded the intended missing behavior: portable recovery absent; access-denied/unavailable and Windows winerror cases escaped as OSError; the existing Windows occupied test escaped with WinError 10013; pipe-select readiness failed with WinError 10038. Unknown-error identity propagation already passed.

Before creating `support.py`, `task-2-red-support.json` additionally recorded the new support tests failing because the helper was absent. Before adding state-error diagnostics, `task-2-red-state-diagnostics.json` recorded the real tiny HTTP child returning a bare HTTP 503 error instead of an assertion with owned logs/directory/last HTTP error. That same case is now green and asserts the child is reaped and both logs are closed.

## Verification commands and results

Every local test used this retained runner, with PowerShell profiles disabled through the command tool's `login=false` option:

```powershell
& 'C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'F:/codex/Project Plan/pr01-implementation/run_retained_tests.py' --source 'F:/codex/Project Plan/pr01-implementation/source' --pattern test_cli.py --report 'F:/codex/Project Plan/pr01-implementation/reports/task-2-complete-cli.json'
& 'C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'F:/codex/Project Plan/pr01-implementation/run_retained_tests.py' --source 'F:/codex/Project Plan/pr01-implementation/source' --pattern test_hosting.py --report 'F:/codex/Project Plan/pr01-implementation/reports/task-2-verified-hosting.json'
& 'C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'F:/codex/Project Plan/pr01-implementation/run_retained_tests.py' --source 'F:/codex/Project Plan/pr01-implementation/source' --pattern test_pipeline.py --report 'F:/codex/Project Plan/pr01-implementation/reports/task-2-green-pipeline.json'
$env:PATH = 'C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin;' + $env:PATH
& 'C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'F:/codex/Project Plan/pr01-implementation/run_retained_tests.py' --source 'F:/codex/Project Plan/pr01-implementation/source' --pattern test_exports.py --report 'F:/codex/Project Plan/pr01-implementation/reports/task-2-complete-exports.json'
```

Earlier iterations used the identical command with these pattern/report pairs:

| Pattern | Report | Result |
| --- | --- | --- |
| test_cli.py | task-2-red-cli.json | Expected RED: 4 tests, 2 failures and 7 subtest/test errors |
| test_cli.py | task-2-red-support.json | Expected RED: 6 tests, 2 failures and 9 subtest/test errors |
| test_cli.py | task-2-green-cli.json | GREEN: 6 tests |
| test_cli.py | task-2-final-cli.json | GREEN: 7 tests |
| test_cli.py | task-2-red-state-diagnostics.json | Expected RED: 7 tests, 1 state-error diagnostic error |
| test_cli.py | task-2-verified-cli.json | GREEN: 7 tests |
| test_hosting.py | task-2-green-hosting.json | GREEN: 8 tests |
| test_exports.py | task-2-green-exports.json | GREEN: 6 tests |
| test_exports.py | task-2-verified-exports.json | GREEN: 6 tests |

Final evidence: CLI 7/7, hosting 10/10, pipeline 27/27, exports 6/6; 50 tests total, no failures/errors/skips. CLI/hosting and CLI/exports were rerun after their final relevant edits. Linux matrix and full suite/watchdog verification belong to the parent integration task and are not claimed here.

## Self-review and limits

- The only production edit is diagnostic classification/formatting and the existing serve exception handler. Unexpected exceptions, Store creation, defaults, demo initialization, and ValueError handling retain their prior behavior.
- Logs use independent read handles, bounded tails and complete startup lines. All real startup-failure cases and normal success assert actual process exit and closed log handles. A tiny child binds but does not listen for the health-timeout case, so the helper cannot accidentally probe an unrelated service.
- In-process cleanup is registered immediately after each owned directory/server construction, before thread start. Store/setup and thread-start failures are exercised; a restart registers separate captured cleanup for both servers.
- The parent's traversal clarification is applied: `private.png` is an existing owned sentinel outside assets, and `/../__main__.py` targets an existing Python file outside WEB. Both return 404 without the sentinel/source content. Original database/project-path examples are also covered.
- HTTP exports use independent expected fields/values, not CSV generated from the production result. Only opaque family IDs are cross-matched to JSON. Excluded and demo rows sharing the categorical palette ensure scope/count assertions can detect unintended leakage.
- Retained local runs intentionally do not certify physical directory or duplicate-upload deletion. The runner archives the duplicate-upload unlink; one referenced asset remains in the test assets directory. Ordinary CI must exercise actual TemporaryDirectory cleanup and unlink behavior. No retention logic or F-drive paths were introduced into production/tests.
- Platform verification here is Windows only. A catastrophic in-process shutdown hang remains covered by the planned suite watchdog; cleanup reports timed-out shutdown/serve threads explicitly rather than silently accepting them.

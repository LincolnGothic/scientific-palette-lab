# Final deadline and portable harness fixes

Scope: five staging source files only: `scripts/verify_distribution.py`, `scripts/run_tests.py`, `tests/test_package.py`, `tests/support.py`, `tests/test_cli.py`. No application, science, frontend, CI/configuration, dependency, or package build changes. No commits, downloads, or deletion. Exact unified diff against parent worktree head `e55b802e1e212dcf09716f452005b73526d5172d`: [final-deadline-fix.diff](final-deadline-fix.diff).

## Installed watchdog ownership

The verifier's installed unit-suite `command` now passes `timeout=None`, relying on the already bounded inner watchdog. Its `--timeout 180` remains unchanged. This removes the redundant outer200-second deadline which could terminate the cleanup owner during metadata30 + worker180 + cleanup15. The regression drives the actual installed-suite command and actual watchdog with a virtual clock and exact mocked owned worker/descendant; other build/install phases are stubbed. It does not sleep minutes or merely assert a constant.

RED: `final-deadline-fix-red.json`,20 tests, one expected regression failure. Retained root `artifacts/cd2ea6a6e8624a7aa2b3aa402ff15586`: metadata ends at30; outer kills watchdog at200; worker and descendant remain marked alive. GREEN source: `final-deadline-fix-green.json`,20/20 (9.979s), retained root `artifacts/2110565375b940cf9afaa52ff7dd59d7`. GREEN existing clean installed runtime: `final-deadline-fix-installed.json`,20/20 (9.589s), retained root `artifacts/eb6f3f67954748888c8ccb1ae1d21f25`. In green virtual evidence worker timeout occurs at210 and owned cleanup finishes at225; failure propagates while timeout report preserves partial testsRun2. Prior unfinished evidence `final-fix-red.json` is retained; resumed red/green reports above establish this completed change.

## Discovery across Python versions

Hosted checkpoint run36867648093 (head07f694c20b83ec09d0ff467196875cec97d63989, tested merge SHA921941d024e885bbe13688b34ee5398bbfc5b26f) failed source suites on Python3.10 baseline/minimum and3.11 because synthetic discovery reused a loader's previous top-level directory. `run_worker` now constructs `unittest.TestLoader()` at the discovery boundary. The new regression seeds the default loader with an unrelated previous root, invokes actual worker discovery in an independent retained root, checks one discovered/executed passing test, and checks global loader state remains unchanged. Existing dynamic counts, zero-suite failure, offline guard and JavaScript consumer cases remain intact.

RED: `discovery-fix-red.json`,21 tests, one expected stale-root ImportError regression failure (local Python3.12 can reproduce it with deliberate state). Retained root `artifacts/0366ddd3f87f460cb9348ad24a81a751`. GREEN: `discovery-fix-green.json`,21/21 (9.769s), retained root `artifacts/233a1cf13b474d57a083760314931f97`.

## Windows log ownership

Hosted Windows source cleanup reported WinError32 after launcher reaping and closed parent streams. Local probes reproduced the lock with a bare ready Python child importing HTTPServer, without helper diagnostics. Plain file-only and naturally exiting child controls passed. Current-process handle census found no surviving parent file handle. Toolhelp process evidence `windows-venv-redirector-probe.json` found the venv launcher PID2604 owning child interpreter23948, while direct bundled Python had no descendant. Closing the parent's process handle and CREATE_NO_WINDOW did not reliably resolve the lock and were not applied. Parent's CPython launcher source inspection corroborates inherited standard handles and a child interpreter/job; our fixture evidence establishes the ownership involved.

Regression RED: `windows-ownership-red.json`,7 tests with four WinError32 error occurrences (failed startup state/HTTP cases and successful startup), retained root `artifacts/aef91e8f31314ffa959f2a9a2819d388`. The strengthened existing tests perform an immediate rename round trip of each exact owned log after server context exit, preserving files and catching handle lifecycle directly without deletion, sleep or weakened cleanup.

The helper now runs `taskkill /PID <exact Popen PID> /T /F` on Windows before reaping a still-running launcher, with10-second command and existing5-second reap waits. It captures command diagnostics, retains nonzero/timeout/unavailable-command failure after bounded parent fallback, and never targets image names or unrelated trees. POSIX termination remains unchanged. Two focused mocked tests verify exact PID arguments/bounds, successful reaping and preserved nonzero/timeout/OSError failures. Existing launch spies record file-backed server streams only, so the additional taskkill subprocess is not misclassified as a server.

Local sandbox denied exact-owned taskkill with `ERROR: Access denied`; this is a permission constraint, not hidden or classified as a helper failure. Retained evidence `artifacts/taskkill-owned-5f1fadcb0215410e9ccc952d94a09369/evidence.json`; exact parent fallback was reaped. Root elevated the bounded retained probe `probe_windows_owned_tree.py`:5/5 passed, all taskkill commands returned0, each output identifies only exact launcher and its child, and both logs immediately renamed round trip. Native ownership evidence: `artifacts/windows-tree-owned-b4cfdae8726f412c9046a2f09e60d954/evidence.json`.

## Commands and limits

Targeted suites used existing retained audit only:

```powershell
& 'D:/Codex_skill/codex-runtimes/pr01-source-audit/Scripts/python.exe' 'F:/codex/Project Plan/pr01-implementation/run_retained_tests.py' --source 'F:/codex/Project Plan/pr01-implementation/source' --pattern test_package.py --report '<named report above>'
& '<existing clean runtime>/venv/Scripts/python.exe' -I 'F:/codex/Project Plan/pr01-implementation/run_retained_tests.py' --source 'F:/codex/Project Plan/pr01-implementation/source' --installed --pattern test_package.py --report 'F:/codex/Project Plan/pr01-implementation/reports/final-deadline-fix-installed.json'
& 'D:/Codex_skill/codex-runtimes/pr01-source-audit/Scripts/python.exe' 'F:/codex/Project Plan/pr01-implementation/run_retained_tests.py' --source 'F:/codex/Project Plan/pr01-implementation/source' --pattern test_cli.py --report 'F:/codex/Project Plan/pr01-implementation/reports/windows-ownership-red.json'
& 'D:/Codex_skill/codex-runtimes/pr01-review-tools/bin/ruff.exe' check <five changed files>
& 'D:/Codex_skill/codex-runtimes/pr01-review-tools/bin/ruff.exe' format --check <five changed files>
```

All five-file Ruff checks pass; all five files already formatted. Node24 executable directory was on local PATH; no assertion about local Node22. Source Python is3.12.14. No repeated distribution build, actual Docker run or newly published CI is claimed. Root is executing elevated covering checks after source freeze; results will be recorded below. Physical temporary-directory deletion/cleanup remains explicitly unverified locally: every artifact and failed-probe file remains retained. Ordinary hosted cleanup and all ten gates for the corrected tested SHA remain parent acceptance work; earlier checkpoint failures are not superseded until that run completes.

## Final frozen-source covering evidence

Root executed the elevated retained source CLI suite after the final test-only rendering correction: `windows-ownership-green.json`,9/9, zero failures/errors/skips, retained root `artifacts/6e394b45ef1047509eab3ef65a59c4d2`. I read this saved report independently. Native failed/successful startup, bounded exact-tree reaping, immediate both-log rename and mocked failure propagation all pass. The initial elevated run's sole assertion failure (expecting str rather than the deliberately preserved repr of TimeoutExpired) is retained as `windows-ownership-first-green-assertion-failure.json`; the native lifecycle cases already passed there. Only that assertion's expected exception rendering changed before the final9/9 run; production did not change. Root separately owns fresh full-suite/installed and hosted matrix acceptance; no uncompleted result is claimed here.

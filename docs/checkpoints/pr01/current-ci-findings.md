# Hosted checkpoint CI findings

Run: https://github.com/LincolnGothic/scientific-palette-lab/actions/runs/36867648093
Implementation head: 07f694c20b83ec09d0ff467196875cec97d63989
Actual tested merge SHA from CI_COMMIT_SHA in job logs: 921941d024e885bbe13688b34ee5398bbfc5b26f

Six of ten jobs passed: Linux Python 3.12 and 3.13, quality, Linux/Windows distribution, Docker. Four source-suite jobs failed; installation succeeded in each.

## Python 3.10 baseline/minimum and Python 3.11

All three share five synthetic-watchdog discovery failures (two failures, three errors). run_worker uses unittest.defaultTestLoader.discover repeatedly in a suite which was itself loaded by that same default loader. The failing consumer regression records ImportError: Start directory is not importable for an independently owned temporary test root. Python 3.12/3.13 do not exhibit the older loader state behavior. Investigate fresh-loader isolation at the discovery boundary; preserve original dynamic-count and offline assertions rather than reducing checks.

Logs: ci-checkpoint-110387085415-failures.log, ci-checkpoint-110387085465-failures.log, ci-checkpoint-110387085664-failures.log.

## Windows

Two errors occur in ordinary TemporaryDirectory cleanup after server-support/startup tests. Both identify server.stderr.log with WinError32; their process and closed-handle assertions passed. Determine which OS handle outlives helper exit. Do not hide cleanup errors or add unconditional sleeps. Under the local deletion restriction, reproduce handle ownership using exact owned-file rename/reopen or handle inspection and retain artifacts; hosted CI establishes ordinary physical cleanup.

Log: ci-checkpoint-110387085603-failures.log.

Final watchdog deadline review finding remains independently required even though both distribution jobs passed on this checkpoint. Root has resumed the original implementer for the deadline and will scope review of all resulting fixes before publication.

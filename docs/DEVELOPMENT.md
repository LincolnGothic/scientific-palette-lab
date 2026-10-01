# Development and engineering verification

Run these commands from the repository root. Python 3.10 or newer is required; the base runtime dependencies are **NumPy >=1.24 and Pillow >=10.1**. Node 22 is the CI verification prerequisite for JavaScript syntax and export tests; running the application needs no Node installation or JavaScript build. No npm packages or frontend framework are involved.

## Clean environments

Create a fresh environment without system site packages. A base install exercises the declared application dependencies without developer tools:

```bash
python3 -m venv .venv/base
.venv/base/bin/python -m pip install .
.venv/base/bin/python -m pip check
.venv/base/bin/python -m palette_lab --help
.venv/base/bin/python -m palette_lab serve
```

Windows PowerShell needs no activation script or Bash for the Python commands:

```powershell
py -3.12 -m venv .\.venv\base
.\.venv\base\Scripts\python.exe -m pip install .
.\.venv\base\Scripts\python.exe -m pip check
.\.venv\base\Scripts\python.exe -m palette_lab --help
.\.venv\base\Scripts\python.exe -m palette_lab serve
```

The installed `palette-lab` console command is equivalent to `python -m palette_lab`. Put global options before the subcommand, for example `python -m palette_lab --data-dir ./another-study serve --port 8766`. Use `serve --demo` for separately labeled synthetic examples. Collection commands described in the [README](../README.md) contact external sources; they are not engineering test prerequisites.

A separate developer environment supplies Ruff, build and PyYAML. The CI constraints pin tools and runtime versions for reproducible engineering runs; they do not replace the public runtime ranges in [pyproject.toml](../pyproject.toml):

```bash
python3 -m venv .venv/dev
.venv/dev/bin/python -m pip install -c ci/constraints.txt setuptools wheel
.venv/dev/bin/python -m pip install -c ci/constraints.txt --no-build-isolation ".[dev]"
.venv/dev/bin/python -m pip check
```

```powershell
py -3.12 -m venv .\.venv\dev
.\.venv\dev\Scripts\python.exe -m pip install -c ci/constraints.txt setuptools wheel
.\.venv\dev\Scripts\python.exe -m pip install -c ci/constraints.txt --no-build-isolation ".[dev]"
.\.venv\dev\Scripts\python.exe -m pip check
```

[ci/constraints.txt](../ci/constraints.txt) selects NumPy 2.2.6 on Python 3.10 and 2.3.5 on newer Python, with Pillow 12.3.0. [ci/constraints-minimum.txt](../ci/constraints-minimum.txt) tests the declared NumPy 1.24.0/Pillow 10.1.0 floors on Python 3.10. For the CI base profile, install constrained `setuptools wheel numpy Pillow` with `--only-binary=numpy,Pillow`, run `pip check`, then install `.` with the same constraints and `--no-build-isolation`, and run `pip check` again. Use the minimum file only with Python 3.10. Base suite jobs do not install `[dev]`.

## Offline tests and adopted quality scope

The full suite uses unittest with a bounded parent watchdog:

```bash
.venv/base/bin/python scripts/run_tests.py --timeout 180 --report ci-results/tests.json
.venv/dev/bin/python -m ruff check palette_lab tests scripts
.venv/dev/bin/python -m ruff format --check scripts tests/support.py tests/test_cli.py tests/test_baseline.py tests/test_exports.py tests/test_package.py palette_lab/__main__.py
node --check palette_lab/web/app.js
bash -n run.sh
```

On Windows, substitute `.\.venv\base\Scripts\python.exe` or `.\.venv\dev\Scripts\python.exe` for the corresponding interpreter. `python -m ruff` avoids a console-script PATH dependency. `bash -n run.sh` needs Bash; the Python application commands do not. Node must be on PATH for the full suite, including generated Python/flowchart export checks.

Lint uses E4, E7, E9, F and RUF100 across `palette_lab`, `tests` and `scripts`. Only the measured legacy `tests/test_pipeline.py` ignores E701/E702; other configured rules still apply there. Format checking adopts the five existing files `palette_lab/__main__.py`, `tests/support.py`, `tests/test_cli.py`, `tests/test_baseline.py` and `tests/test_exports.py`, plus `tests/test_package.py` and the three scripts. Do not infer repository-wide formatting adoption from this scope.

The runner prohibits the real `Remote.get` during discovery and execution and records attempts even if a test catches the rejection. Source parser fixtures and fake remotes require no live acquisition. This guard covers the application's acquisition path, not arbitrary network access. Dependency installation and GitHub infrastructure can require network access.

The runner exits nonzero on failures, errors, empty discovery, acquisition attempts, missing/invalid worker evidence or timeout. Its report exposes `status`, `discovered`, `testsRun`, `failures`, `errors`, `skips`, `duration`, `remote_attempts`, `package_origin` and, when export tests are loaded, `export_asset`. The watchdog also records `unfinished`, `timeout_seconds`, `returncode`, `watchdog_duration`, log paths/tails and termination diagnostics when needed. Unavailable counts remain null or absent, never zero by assumption. Skips are reported separately; inspect them before accepting a run.

Tests create owned temporary directories and subprocesses and normally clean up their temporary files. On machines requiring approval before deletion, arrange that approval for exact targets or use an independently documented retained audit. A retained local run does not verify ordinary physical cleanup. The committed runner has no retention switch. Hosted CI must exercise its ordinary cleanup and watchdog behavior.

## Distribution and hosting checks

Use the developer interpreter below (the commands use `python` for brevity). On Windows, use `.\.venv\dev\Scripts\python.exe`. Build into a fresh output directory so the verifier finds exactly one wheel and one sdist; retain previous outputs rather than silently cleaning them:

```bash
python -m build --no-isolation
python scripts/verify_distribution.py --dist dist --report ci-results/distribution.json
python scripts/check_hosting.py --report ci-results/hosting-static.json
```

The default `build` operation builds the sdist and then builds the wheel from that sdist. The verifier audits package module/resource bytes, metadata and entry points against checkout, creates a clean runtime venv **outside checkout**, installs constrained declared runtime dependencies followed by the exact wheel with `--no-deps`, and runs `pip check`. It rejects developer packages in that runtime, checks isolated import origin, both help paths, all three web assets, demo/real separation and an owned local server's health/state/static responses. It then runs the same full offline tests with isolated installed imports and the installed `app.js` consumer path. It requires Node on PATH but no dev extras in the runtime venv.

`distribution.json` contains `environment`, `artifact_root`, `cleanup` and `checks`. Check names are `build`, `archives`, `venv`, `install`, `origin`, `resources`, `help`, `demo`, `server` and `unit_suite`. Build is recorded as **external**, requiring the preceding build log; archive presence alone proves no build execution. Failed or timed-out phases include `error`, later phases remain `unexecuted`, and the process exits nonzero. The installed suite is linked by `checks.unit_suite.report` and embedded at `checks.unit_suite.result`. Runtime artifacts are retained outside checkout; this retention is separate from normal test temporary-file cleanup.

Static hosting validation parses [render.yaml](../render.yaml) with PyYAML and checks the existing single Docker service, branch, plan, health path, instance count, persistent disk and four environment entries, including a required password secret with no literal value. Static agreement does not prove Render deployability.

With a local Docker daemon, build and check an owned container:

```bash
docker build --pull --progress=plain --tag palette-lab-ci .
python scripts/check_hosting.py --docker palette-lab-ci --report ci-results/docker.json
```

The workflow additionally captures build output in `ci-results/docker-build.log`. The checker reads that sibling log for the `python:3.12-slim` base digest; if absent it reports unknown. Docker evidence includes image ID/digests, runtime versions/freeze, minimal health, unauthenticated 401 and authenticated empty-real state. It uses public dummy credentials and a dynamic loopback port, captures container logs, and bounds stop/force-stop operations to its own UUID name, including uncertain launch failures. It retains artifacts and reports cleanup/log errors. It performs no deployment. The floating Docker base and dependency resolution remain a reproducibility limit.

Hosting JSON has independent `render.status` and `docker.status` fields. Without `--docker`, Docker stays `unexecuted` even when top-level `status` is `passed`. With Docker requested, smoke failure makes the command fail. See [HOSTING.md](HOSTING.md) for application hosting instructions.

## Evidence and acceptance

Use [Engineering CI workflow runs](https://github.com/LincolnGothic/scientific-palette-lab/actions/workflows/ci.yml). Select the run associated with the current implementation head and confirm the actual tested SHA: pull-request runs may test a merge commit. The final PR description must identify the reviewed base, implementation head, tested SHA and exact accepted run URL. A green older run does not establish the current head.

The workflow requires Linux Python 3.10/3.11/3.12/3.13 baseline cells, Windows Python 3.12, a Linux Python 3.10 minimum-runtime cell, quality, Linux/Windows distribution and Docker. Inspect each required job and its logs; diagnostic uploads use `always()` and their presence alone does not establish success.

| Artifact name | Evidence inside |
|---|---|
| `tests-ubuntu-24.04-3.10-baseline` (and corresponding OS/Python/profile names) | `tests.json`, uniquely named `tests.worker-<uuid>.json`, `tests.stdout.log`, `tests.stderr.log` |
| `quality` | `hosting-static.json`; Ruff, export, Node and Bash outcomes are in job logs |
| `distribution-ubuntu-24.04`, `distribution-windows-2022` | wheel/sdist, `distribution.json`, `distribution.installed-tests.json`, its unique worker JSON and stdout/stderr logs |
| `docker` | `docker-build.log`, `docker.json`, `docker.container.log` when captured |

Environment records include platform/architecture, Python executable/version, dependency versions, tool command results, runner image metadata and `tested_commit_sha` from `CI_COMMIT_SHA`. Local runs without that variable report an unknown SHA. Derive current counts from each successful source/installed report, reconcile discovery/execution and inspect failures/errors/skips and acquisition attempts; do not maintain a manually fixed current total here.

The historical release record and its independent Windows review are in [VALIDATION.md](../VALIDATION.md). Local retained fixture/code checks do not attest hosted CI, actual Docker or ordinary physical cleanup. Those gates remain pending until their corresponding published run succeeds. Engineering contracts protect current color extraction/matching, statistics, recommendation, review/storage and export behavior; they do not establish real-world extraction accuracy or a representative scientific benchmark. Acquisition pilots and browser observations remain separate historical evidence.

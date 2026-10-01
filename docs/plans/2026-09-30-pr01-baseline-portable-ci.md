# PR #01 — Baseline, Portable Checks, and Engineering CI: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking. Implementation requires the user's separate authorization; this review authorizes no repository modification, branch creation, merge, push, or deployment.

**Goal:** Establish a reproducible cross-platform v0.1 engineering baseline before PR #02 changes database architecture.

**Architecture:** Retain unittest, the existing Python/SQLite application and plain JavaScript. Add test-only subprocess support, compact scientific regression fixtures, package verification and a conservative GitHub Actions workflow. Restrict production edits to accurate CLI error diagnostics, one unused import needed for lint adoption, and a corrected dependency minimum.

**Tech stack:** Python 3.10–3.13; NumPy/Pillow as the only scientific runtime dependencies; unittest/stdlib; Node for syntax/export testing; Ruff, build and PyYAML as development tools; GitHub Actions; Docker on a Linux CI runner.

**Spec:** [User's complete planning request](<C:/Users/Lenovo/.codex/attachments/e962c247-37bd-42aa-9a8b-1c6a4a1e4e50/Pasted text.txt>) and [the corrected roadmap in PR #1](https://github.com/LincolnGothic/scientific-palette-lab/blob/7512d322a4df174d3e30c9604d193b6479d35abf/docs/reviews/2026-09-30/scientific-palette-lab-improvement-plan.md).

**Review date:** 30 September 2026, America/Los_Angeles.

**Exact main/application commit reviewed:** `192abce8f86777911df0e1b4d62340c2a19e92f5`.

**Exact documentation PR #1 head reviewed:** `7512d322a4df174d3e30c9604d193b6479d35abf`. PR #1 remains draft, open, mergeable and unmerged; its three changed files are documentation. Do not confuse roadmap “PR 01” with GitHub pull request number 1.

**Status:** Detailed engineering review and proposed implementation only. No application/repository files or GitHub state were changed. Audit scripts/results are separate local artifacts. None of the proposed CI, packaging, diagnostics or regression tests below has been implemented.

## Global constraints

- **PR #01 must improve verification infrastructure without changing the scientific behavior of the application.**
- **Do NOT begin implementation yet.**
- Linux: Python 3.10, 3.11, 3.12 and 3.13. Windows: at least Python 3.12.
- Keep unittest. No new scientific algorithm, schema migration, data model or API semantics.
- Preserve the 55/30/15 recommendation baseline and the reference-palette penalty.
- No npm dependency management, React, Vite, Webpack, TypeScript or frontend framework.
- No normal test depends on live acquisition, publisher websites, models or paid services. Dependency installation and GitHub infrastructure are separate from test-time source acquisition.
- No code-license metadata until the owner selects a license. No Render deployment or hosting charges.
- Do not delete files/folders in bulk. On the user's machine, list exact deletion targets/reasons and obtain explicit yes/no permission; retain audit artifacts otherwise.
- Do not include PR #02 work. All future corpus, study/history, vector, CIEDE2000, AI, confidence, benchmark tooling, recoloring, account and framework work remains outside this PR.

## A. Current-state assessment and fresh evidence

The repository is small and suitable for a full Windows suite. It has 35 tests: 27 pipeline tests, six hosting/security tests and two CLI tests. A fresh Windows audit completed in approximately 7.6 seconds and reproduced **33 passed, one failed, one errored**. This is not a green baseline.

| Area inspected | Actual current behavior | PR #01 implication |
|---|---|---|
| `__main__.py:main()` | Builds Store before starting; handles ValueError and only EADDRINUSE during serve | Preserve initialization/command semantics; improve recognized OS diagnostics |
| `app.py:serve()` | ThreadingHTTPServer, port 0 supported, actual port printed with flush; KeyboardInterrupt closes server | No new startup endpoint or port allocator needed |
| `app.py:handler_for()` | Authentication, host/origin checks, unauthenticated minimal /health, current JSON/CSV exports | Protect existing HTTP behavior through integration tests |
| `colors.py` | White alpha compositing, weighted raster/Lab merging, ΔE76 bottleneck matching, existing CVD matrices | Keep implementation byte-for-byte unchanged |
| `statistics.py` | Count/encoding buckets, greedy complete-link grouping, distinct-variant medoid, paper votes; journal/year fields count panels | Pin these specific semantics, including conditional denominators |
| `recommend.py` | Exact locked color, warnings for low contrast, categorical/fill CVD filter; 55/30/15 and reference penalty 0.05 | Background contrast is a warning/score input, not a new hard exclusion |
| `store.py` | Five tables: papers, figures, panels, reviews, runs; WAL; review revisions and paper eligibility | No schema/history redesign; keep current review effects |
| `web/app.js:downloadCode()` | Categorical Python; sequential/diverging Python; flowchart role JSON | Flowchart export is JSON, not Python; all branches can be tested without frontend edits |
| `pyproject.toml` | Python >=3.10, NumPy >=1.24, Pillow >=10; setuptools >=68; web/* package data | Flat current assets covered; installed distribution still needs proof |
| `demo.py:seed_demo()` | 12 reviewed synthetic paper/panel examples; ImageFont.load_default(size=20) | Pillow minimum is too low for this already-used API |
| `run.sh` | Bash wrapper with venv/Python/Codex fallback; no Windows PowerShell launcher | Keep wrapper; document portable python -m invocation on Windows |
| Dockerfile | Python 3.12-slim; copies package and installs base project; starts serve | Test current image; no hosting redesign |
| render.yaml | One Docker web service, 0.5c-512mb, /health, one instance, /var/data 1 GB disk, password sync:false | YAML parses; add bounded static expectations, never deploy |
| README / VALIDATION | Useful definitions; VALIDATION accumulates historical 27/29/35-test claims | Separate historical observations from generated current CI evidence |
| GitHub | Zero workflow runs and zero main-commit statuses; no tracked .github workflow | Create engineering CI; there is no independent CI evidence today |

Additional fresh checks:

- Node syntax check passed.
- Existing categorical/sequential/diverging exports produced real newlines and valid Python AST/compilation. Flowchart JSON preserved HEX order, roles and origin.
- A separate test-only source-package startup probe used file logs and port 0 successfully. /health, demo/real state and static assets responded; demo had 12 papers/panels/reviewed items and real had zero.
- Ruff 0.13.3, explicitly selecting E4/E7/E9/F, found 32 issues: five F401, one F811, 17 E702, nine E701. All compact-statement issues are in tests/test_pipeline.py. Ruff format would change 15 of 16 Python files; no formatting was applied.
- PyYAML 6.0.3 parsed render.yaml successfully. This was local syntax/static review, not Render's service-side validation.
- The read-only checkout remained clean at the reviewed SHA.

Limits: only Windows Python 3.12.14, NumPy 2.3.5 and Pillow 12.3.0 were executed. Temporary directories and duplicate-asset unlinks were retained to honor deletion rules; cleanup was not validated. No fresh wheel/sdist build, clean installed-wheel test, Linux/macOS run or Docker build was performed. Docker is unavailable locally.

Evidence: [engineering summary](<F:/codex/Project Plan/pr01-review/engineering-review-verification.json>), [full test/socket traces](<F:/codex/Project Plan/pr01-review/baseline-audit.json>), [startup probe](<F:/codex/Project Plan/pr01-review/startup-probe.json>), [scientific probes](<F:/codex/Project Plan/pr01-review/science-probe.json>), [export probes](<F:/codex/Project Plan/pr01-review/export-probe.json>).

## B. Root causes of the Windows failures

### Failure A: occupied-port test

Trace: CLI main → app.serve → ThreadingHTTPServer constructor → HTTPServer.server_bind → TCPServer.server_bind → **socket.bind()**. The failing operation is bind, not HTTP polling, listen, SQLite or a request handler.

The existing test owns a listening socket on 127.0.0.1 and an OS-assigned port. Its default socket has SO_REUSEADDR=0 and SO_EXCLUSIVEADDRUSE=0. HTTPServer enables address reuse. On the audited machine, changing only the second socket's reuse setting changed the result:

| First listening socket | Second socket reuse | Observed result |
|---|---:|---|
| Default options | 0 | errno/winerror 10048, address already in use |
| Default options | 1 | errno 13, winerror 10013, access denied |
| Exclusive option | 0 | 10048 |
| Exclusive option | 1 | 10013 |
| Reuse option | 0 | 10048 |
| Reuse option | 1 | Bind succeeded; address sharing is possible |

Direct ThreadingHTTPServer construction against the default listener reproduced errno 13 / winerror 10013 with allow_reuse_address=1. Therefore this audit's 10013 is induced by the known live listener and Windows reuse rules. It is not evidence of a general filesystem permission problem or a missing administrator privilege. The probes do not identify every machine's Windows policy or security product.

Microsoft defines 10013 as access denied and describes exclusive listeners/drivers as possible causes. Reserved/excluded ports and system policy can also yield access-denied binding. Consequently, **10013 alone cannot establish that a port is occupied**. A production connect probe would also fail to distinguish all causes and should not be added. [Winsock codes](https://learn.microsoft.com/en-us/windows/win32/winsock/windows-sockets-error-codes-2), [reuse/exclusive behavior](https://learn.microsoft.com/en-us/windows/win32/winsock/using-so-reuseaddr-and-so-exclusiveaddruse), [excluded-port example](https://learn.microsoft.com/en-us/troubleshoot/windows-server/networking/error-10013-wsaeacces-is-returned).

Classification: a combination of Windows socket behavior, a CLI diagnostic gap and an overly specific test assumption. The fixture correctly creates an occupied endpoint. Its assumption that this must produce only an “already in use” diagnosis is not portable.

Do not change production SO_REUSEADDR/SO_EXCLUSIVEADDRUSE settings to manufacture a preferred errno. Do not relabel EACCES as EADDRINUSE. Keep the existing listener alive.

### Failure B: available-port startup test

tests/test_cli.py lines 43–47 pass a subprocess stdout pipe to select.select(). Windows select accepts sockets, not pipe handles, producing WSAENOTSOCK 10038 before the test can read the announced URL. This is a **test portability bug**; the separate startup probe demonstrated that the existing server starts on Windows. [Python select documentation](https://docs.python.org/3/library/select.html).

The current POSIX approach has another weakness: readiness for some pipe bytes does not guarantee readline can immediately read a full newline-terminated line. Pipe readiness followed by an unbounded readline is not a sufficient timeout guarantee.

## C. Exact proposed implementation and independently reviewable tasks

Every task below is future work. Freeze baseline fixtures before production diagnostic edits. Newly introduced test helpers are infrastructure, not application services.

### Task 1: Freeze scientific and export contracts

**Files:** create tests/test_baseline.py, tests/fixtures/v01-scientific.json, tests/test_exports.py and tests/export_harness.cjs. Keep tests/test_pipeline.py's meaningful existing assertions; its narrow import cleanup belongs to Task 3.

**Interfaces:** BaselineTests uses a test-only Rows object with panels(dataset) returning explicit immutable panel dictionaries. ExportTests invokes Node with timeout=10 and consumes a JSON envelope of generated content/filename for each case. HTTP exports use the shared server fixture from Task 2 when available.

- [ ] Add the explicit fixtures and assertions in §E; expected scientific values must have a written rationale.
- [ ] Run baseline tests against unmodified main. They must pass before a production edit is permitted.
- [ ] Add the Node VM harness described below, testing the actual downloadCode body rather than a copied generator.
- [ ] Parse/compile Python exports; JSON-decode flowchart output; verify actual HTTP CSV/JSON exports against small reviewed fixtures.
- [ ] Run all existing pipeline/security tests. Keep the two known CLI failures recorded separately until Task 2.

Concrete alpha test content:

```python
image = Image.new("RGBA", (40, 20), (0, 0, 255, 0))
image.paste((255, 0, 0, 128), (0, 0, 20, 20))
image.paste((0, 0, 255, 255), (20, 0, 30, 20))
image.save(path)
result = extract_palette(path)
self.assertEqual([c["hex"] for c in result["colors"]], ["#FF7F7F", "#0000FF"])
self.assertEqual([c["weight"] for c in result["colors"]], [0.666667, 0.333333])
self.assertEqual(result["detected_count"], 2)
self.assertEqual(result["method"], "weighted-raster-lab-v1")
self.assertEqual(result["confidence"], "low")
```

Node can evaluate the existing function without restructuring the frontend. Locate the exact start marker async function downloadCode(row) and the next document.addEventListener('click' marker; reject missing/ambiguous markers. vm.runInContext that source slice with timeout=1000, globals kind/dataset/recOptions, and tiny Blob/URL/document.createElement/setTimeout stubs. Capture Blob content and link.download. No DOM library, npm packages or application source extraction is needed. A later function relocation must break this harness clearly rather than silently test a stale copy. The audit already exercised this strategy successfully.

Concrete Python export assertions:

```python
tree = ast.parse(content)
compile(content, filename, "exec")
assign = next(
    node for node in tree.body
    if isinstance(node, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "colors" for t in node.targets)
)
self.assertEqual(ast.literal_eval(assign.value), expected_hex_order)
self.assertIn("\n", content)
self.assertNotIn("\\n", content)
```

Check the categorical cycler call and ordered LinearSegmentedColormap.from_list call through AST, not only substrings. Flowchart output is JSON with kind, origin, colors and roles. Do not compile it as Python. Matplotlib/cycler are dependencies of the generated user code, not new base application dependencies; syntax/structure checks do not require installing them.

**Verification commands:** python -m unittest discover -s tests -p test_baseline.py -v; python -m unittest discover -s tests -p test_exports.py -v. Run with Node on PATH. Scientific baseline tests can run without Node; ExportTests must fail clearly when invoked without its documented Node prerequisite, rather than silently skipping in CI.

### Task 2: Portable startup, accurate diagnostics and bounded isolation

**Files/functions:** modify tests/test_cli.py:StartupTests, palette_lab/__main__.py:main's OSError handler; create tests/support.py. Modify tests/test_hosting.py:setUp/start_server/stop_server and tests/test_pipeline.py:setUp/tearDown only for cleanup registration/isolation. Do not change app.serve or socket reuse policy.

**Interfaces:** support.running_server(command, cwd, directory, env, startup_timeout=30) yields a URL and process diagnostics; it owns the Popen and closes log handles. support.stop_process(process) uses terminate/wait(5), then kill/wait(5), and reports failure to reap. An internal wait_for_url(process, stdout_path, stderr_path, deadline) polls complete startup lines and early process exit.

- [ ] First add mocked EADDRINUSE/EACCES/EPERM/EADDRNOTAVAIL, Windows 10048/10013/10049 and unknown-error cases. Prove that current CLI fails the access-denied diagnostics requirement.
- [ ] Replace pipe select/readline with the file-log polling approach in §G, then verify both existing CLI tests on Windows/Linux.
- [ ] Apply only the recognized-error diagnostic change in §H; preserve unexpected exceptions and existing conflict recovery text.
- [ ] Make the occupied test assert accurate OS-specific outcomes and an independently reachable existing listener. Optionally set SO_EXCLUSIVEADDRUSE on the Windows test listener before binding to prevent sharing; do not change production options.
- [ ] Clear inherited PORT/PALETTE_* and RENDER_EXTERNAL_URL values for subprocess tests, set the data directory explicitly, use loopback and --port 0, and force UTF-8/unbuffered output.
- [ ] Register cleanup immediately after resource acquisition using addCleanup or ExitStack. A Store/setup failure must not bypass temporary-directory cleanup. Shutdown servers before closing/removing their owned SQLite/assets/log directories.
- [ ] Verify timeout/early-exit/no-startup-line cases with tiny child commands; no intentional orphan process is acceptable.

For CLI error-code tests, patch serve with the specified OSError and set sys.argv to a temporary --data-dir serve invocation. Assert SystemExit(1), stderr category/raw OS code/recovery text, and no traceback for recognized failures. For unknown errors, assert that the same exception propagates. This avoids assuming that a CI user can reproduce privileged-port denial.

In HostingTests, preserve current tests and add HTTP assertions: unauthenticated /style.css and /api/export.csv return 401; malformed Basic/Bearer credentials at /api/state return 401; authenticated /assets/%2e%2e/palette.sqlite3 and /../pyproject.toml return 404 without exposing bytes. Use http.client to preserve the actual traversal request path. Foreign-host health requests remain 403, while an allowed-host unauthenticated /health returns only {"status":"ok"}. These are tests of existing gates; do not change routing/authentication in this PR.

Temporary directories belong to each test; no fixture uses the repository's data directory. On CI use TemporaryDirectory under RUNNER_TEMP and keep the finalizer registered. Windows files/connections/Popen handles must close before directory cleanup. Do not “fix” unconfirmed sandbox ACL issues with chmod, elevated production permissions or weakened security.

On this user's local machine, a retained audit run or explicit approval for enumerated deletion targets is required. A retained run cannot certify directory/duplicate-upload deletion. Ordinary CI should exercise actual test-owned cleanup and verify that duplicate uploads leave one referenced asset; no production cleanup logic needs to be added.

**Verification commands:** python -m unittest discover -s tests -p test_cli.py -v; python -m unittest discover -s tests -p test_hosting.py -v; full suite through the watchdog runner introduced in Task 4.

### Task 3: Minimal lint adoption and dependency metadata

**Files/functions:** modify pyproject.toml; remove only unused eligible_panels from app.py's statistics import; remove unused json, urllib.parse, suggest_panels and validate_bbox imports in tests/test_pipeline.py. Removing unused json also removes the F811 conflict with FakeRemote.json.

- [ ] Keep scientific source bodies unchanged. Run all baseline fixtures before and after the import-only edit.
- [ ] Raise the declared Pillow floor from >=10 to **>=10.1**; do not alter demo rendering or add a fallback font.
- [ ] Add optional dev dependencies: Ruff==0.13.3, build==1.3.0, PyYAML==6.0.3. Base dependencies remain NumPy and Pillow only.
- [ ] Adopt explicit E4/E7/E9/F lint rules across palette_lab, tests and scripts, with RUF100 to detect obsolete suppressions.
- [ ] Document the two narrow legacy formatting exceptions below; no F-rule blanket ignore.
- [ ] Format only newly created infrastructure/test files and the small CLI files being rewritten; do not run ruff format over the repository.

Pillow 10.1 introduced the font-size API already called by seed_demo. Correcting dependency metadata fixes a known install-compatibility gap; it does not change the implemented font choice or scientific algorithms. [Pillow 10.1 notes](https://pillow.readthedocs.io/en/stable/releasenotes/10.1.0.html).

Proposed configuration:

```toml
[project.optional-dependencies]
dev = ["ruff==0.13.3", "build==1.3.0", "PyYAML==6.0.3"]

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "RUF100"]

[tool.ruff.lint.per-file-ignores]
"tests/test_pipeline.py" = ["E701", "E702"]
```

E701 means multiple statements after a colon; E702 means semicolon-separated statements. Both exceptions apply only to the measured compact legacy test file, preserving its current style rather than rewriting it. There are no global ignores and no F401/F811 ignore. New tests go into normally linted/formatted files. E501/import sorting/large optional rule collections are not enabled initially, because they do not establish this baseline and would add unrelated churn. [Ruff configuration](https://docs.astral.sh/ruff/configuration/).

Format checks explicitly name scripts, tests/support.py, the new test modules, tests/test_cli.py and palette_lab/__main__.py. Historical app/hosting/pipeline/scientific modules remain outside the initial formatter scope even when a small import/fixture line is touched; lint still checks them. Document this boundary in DEVELOPMENT.md rather than claiming repository-wide formatting compliance.

Do not add a pytest migration, runtime test framework, code-license metadata or unneeded project classifiers/URLs. These metadata additions can be separate owner decisions. Existing setuptools packaging and web/* configuration stay unless distribution verification demonstrates a current omission.

### Task 4: Test watchdog, distribution checks, hosting checks and CI

**Create:** scripts/run_tests.py, scripts/verify_distribution.py, scripts/check_hosting.py, ci/constraints.txt, ci/constraints-minimum.txt, .github/workflows/ci.yml. Their concrete jobs/commands are specified in §D and §F.

**Interfaces:**

- run_tests.py --timeout SECONDS --report PATH [--worker]: a parent watchdog invokes the worker, which discovers the repository's tests and writes unittest counts/environment JSON. Exit nonzero on failed/error/timeout, or if no tests were discovered.
- verify_distribution.py --dist DIST_DIR --report REPORT_PATH: inspect wheel/sdist, create a clean venv/work directory, install only wheel plus declared runtime requirements, check resources, CLI help, demo/server and the same full test suite against the installed package. It resolves project paths from __file__, never from caller cwd.
- check_hosting.py --report REPORT_PATH [--docker IMAGE_TAG]: always validate local Render YAML expectations; with --docker, run an already-built local image, query health/authenticated state, capture logs and stop only its own container.

- [ ] Implement dynamic unittest counts and the bounded watchdog protocol in §D; exercise no-tests, failure, early exit and timeout cases.
- [ ] Add read-only archive/resource checks, clean installed-wheel smoke and installed-suite execution in §F.
- [ ] Add exact local Render assertions; implement the Docker smoke protocol in §D using only dummy local credentials.
- [ ] Add pinned CI constraints and full Linux/Windows jobs. All failures must propagate; never continue-on-error a required check.
- [ ] Emit reports before exit, upload diagnostics with always(), and label timed-out/unexecuted checks accurately.
- [ ] Run the workflow on the future implementation PR and wait for every required cell.

This is verification tooling, not an experiment-manifest system. Build tools/Ruff/PyYAML must not leak into the clean runtime venv, apart from pip/venv tooling. No caching initially: this small project gains more from understandable cold installs than cache invalidation machinery.

### Task 5: Document and audit the finished PR

**Files:** create docs/DEVELOPMENT.md; modify README.md and VALIDATION.md. Do not overwrite the historic roadmap/audit to pretend it was green.

- [ ] Document clean installation, Windows python -m commands, dev setup, adopted Ruff scope, offline tests, Node prerequisite, package checks and evidence locations.
- [ ] Relabel historical VALIDATION sections and link current CI run/artifact evidence; derive current counts from reports instead of manually editing totals.
- [ ] Compare scientific fixtures before/after and examine the production diff line-by-line. Algorithm/storage/demo/frontend bodies must remain unchanged.
- [ ] Confirm all required checks and scope checklist in §L before requesting merge.

## D. Proposed CI workflow and commands

Four required job families are enough. No acquisition canary is necessary for PR #01; a later manual/scheduled non-blocking canary is a separate workflow and report.

| Job | Runner/Python | Commands and dependency scope | Failure behavior |
|---|---|---|---|
| tests | ubuntu-24.04 × 3.10/3.11/3.12/3.13; windows-2022 × 3.12 | Create a fresh venv with system-site-packages disabled; install the base project; run full unittest suite with 180-second watchdog | fail-fast:false; every cell required; report partial results/timeout |
| minimum-runtime | ubuntu-24.04 / 3.10 | NumPy 1.24.0, Pillow 10.1.0; same base tests plus demo/resource checks | Required compatibility check of declared floors; no source-build surprise |
| quality | ubuntu-24.04 / 3.12 and Node 22 | dev tools; Ruff lint/adopted format, node --check, export tests, static Render checks, bash -n run.sh | Any required command failure fails job |
| distribution | ubuntu-24.04 / 3.12 and windows-2022 / 3.12 | Build wheel+sdist; verify archives; clean venv install; installed full suite and demo/server/console smoke | Wheel masking, omissions, install/start failure all fail |
| docker | ubuntu-24.04 / 3.12 | docker build current Dockerfile; local container health/auth smoke | Required build/smoke; no Render, registry push or secrets |

The minimum-runtime check is a sixth tests-matrix cell in the YAML below, not a new framework. It catches the discovered metadata defect and establishes that a larger preloaded runtime is unnecessary.

Proposed reviewed CI dependency pins:

```text
# ci/constraints.txt: CI reproducibility, not a replacement for public dependency ranges
numpy==2.2.6; python_version < "3.11"
numpy==2.3.5; python_version >= "3.11"
Pillow==12.3.0
setuptools==80.9.0
wheel==0.45.1
build==1.3.0
packaging==25.0
pyproject-hooks==1.2.0
ruff==0.13.3
PyYAML==6.0.3
tomli==2.2.1; python_version < "3.11"
colorama==0.4.6; sys_platform == "win32"
```

ci/constraints-minimum.txt uses the same build/tool pins but NumPy==1.24.0 and Pillow==10.1.0 for Python 3.10. Python 3.10 needs an older supported NumPy series; 2.2.6 supports Python 3.10–3.13. Pillow 12.3.0 declares >=3.10. Pins on the higher Python versions preserve the dependency versions actually exercised in this Windows review. All proposed pins must be verified on hosted runners; none makes an unrun matrix “passed.” [NumPy 2.2.6](https://numpy.org/doc/stable/release/2.2.6-notes.html), [Pillow 12.3 metadata](https://github.com/python-pillow/Pillow/blob/12.3.0/pyproject.toml).

Install setuptools/wheel/runtime prerequisites first with these constraints; then install the project with --no-build-isolation so an unconstrained ephemeral build backend does not bypass the pins. pip check after each install. The tests job must not install dev extras. Use wheels for NumPy/Pillow through --only-binary=numpy,Pillow; a missing supported wheel is a real install failure to diagnose, not an implicit compiler dependency.

The following is a concrete proposed workflow. Scripts it calls have the contracts above and protocols below; it is not a workflow currently present in the repository.

```yaml
name: Engineering CI
on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: engineering-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
defaults:
  run:
    shell: bash
env:
  PYTHONDONTWRITEBYTECODE: "1"
  PYTHONUTF8: "1"
  PYTHONUNBUFFERED: "1"
  CI_COMMIT_SHA: ${{ github.sha }}
jobs:
  tests:
    name: tests-${{ matrix.os }}-py${{ matrix.python }}-${{ matrix.profile }}
    runs-on: ${{ matrix.os }}
    timeout-minutes: 10
    strategy:
      fail-fast: false
      matrix:
        include:
          - {os: ubuntu-24.04, python: "3.10", profile: baseline, constraints: ci/constraints.txt}
          - {os: ubuntu-24.04, python: "3.11", profile: baseline, constraints: ci/constraints.txt}
          - {os: ubuntu-24.04, python: "3.12", profile: baseline, constraints: ci/constraints.txt}
          - {os: ubuntu-24.04, python: "3.13", profile: baseline, constraints: ci/constraints.txt}
          - {os: windows-2022, python: "3.12", profile: baseline, constraints: ci/constraints.txt}
          - {os: ubuntu-24.04, python: "3.10", profile: minimum, constraints: ci/constraints-minimum.txt}
    steps:
      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # reviewed v5
        with: {persist-credentials: false}
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # reviewed v6
        with: {python-version: "${{ matrix.python }}"}
      - name: Create isolated Python environment
        run: |
          python -m venv "$RUNNER_TEMP/palette-ci"
          python - <<'PY'
          import os
          from pathlib import Path
          directory = Path(os.environ["RUNNER_TEMP"]) / "palette-ci"
          scripts = directory / ("Scripts" if os.name == "nt" else "bin")
          with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as target:
              target.write(str(scripts) + "\n")
          PY
      - uses: actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444 # reviewed v5
        with:
          node-version: "22"
          package-manager-cache: false
      - name: Install base only
        run: |
          python -m pip install -c "${{ matrix.constraints }}" --only-binary=numpy,Pillow setuptools wheel numpy Pillow
          python -m pip install -c "${{ matrix.constraints }}" --no-build-isolation .
          python -m pip check
      - name: Full offline suite
        run: python scripts/run_tests.py --timeout 180 --report ci-results/tests.json
      - uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # reviewed v4
        if: always()
        with:
          name: tests-${{ matrix.os }}-${{ matrix.python }}-${{ matrix.profile }}
          path: ci-results/
          if-no-files-found: warn
  quality:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09
        with: {persist-credentials: false}
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1
        with: {python-version: "3.12"}
      - name: Create isolated Python environment
        run: |
          python -m venv "$RUNNER_TEMP/palette-ci"
          python - <<'PY'
          import os
          from pathlib import Path
          directory = Path(os.environ["RUNNER_TEMP"]) / "palette-ci"
          scripts = directory / ("Scripts" if os.name == "nt" else "bin")
          with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as target:
              target.write(str(scripts) + "\n")
          PY
      - uses: actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444
        with: {node-version: "22", package-manager-cache: false}
      - name: Install developer tools
        run: |
          python -m pip install -c ci/constraints.txt setuptools wheel
          python -m pip install -c ci/constraints.txt --no-build-isolation ".[dev]"
          python -m pip check
      - run: ruff check palette_lab tests scripts
      - run: ruff format --check scripts tests/support.py tests/test_cli.py tests/test_baseline.py tests/test_exports.py tests/test_package.py palette_lab/__main__.py
      - run: node --check palette_lab/web/app.js
      - run: python -m unittest discover -s tests -p test_exports.py -v
      - run: bash -n run.sh
      - run: python scripts/check_hosting.py --report ci-results/hosting-static.json
      - uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        if: always()
        with: {name: quality, path: ci-results/, if-no-files-found: warn}
  distribution:
    runs-on: ${{ matrix.os }}
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix: {os: [ubuntu-24.04, windows-2022]}
    steps:
      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09
        with: {persist-credentials: false}
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1
        with: {python-version: "3.12"}
      - name: Create isolated Python environment
        run: |
          python -m venv "$RUNNER_TEMP/palette-ci"
          python - <<'PY'
          import os
          from pathlib import Path
          directory = Path(os.environ["RUNNER_TEMP"]) / "palette-ci"
          scripts = directory / ("Scripts" if os.name == "nt" else "bin")
          with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as target:
              target.write(str(scripts) + "\n")
          PY
      - uses: actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444
        with: {node-version: "22", package-manager-cache: false}
      - name: Build both distributions
        run: |
          python -m pip install -c ci/constraints.txt setuptools wheel build
          python -m build --no-isolation
      - run: python scripts/verify_distribution.py --dist dist --report ci-results/distribution.json
      - uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        if: always()
        with:
          name: distribution-${{ matrix.os }}
          path: |
            dist/
            ci-results/
          if-no-files-found: warn
  docker:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09
        with: {persist-credentials: false}
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1
        with: {python-version: "3.12"}
      - name: Create isolated Python environment
        run: |
          python -m venv "$RUNNER_TEMP/palette-ci"
          python - <<'PY'
          import os
          from pathlib import Path
          directory = Path(os.environ["RUNNER_TEMP"]) / "palette-ci"
          scripts = directory / ("Scripts" if os.name == "nt" else "bin")
          with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as target:
              target.write(str(scripts) + "\n")
          PY
      - run: python -m pip install -c ci/constraints.txt PyYAML
      - run: docker build --pull --progress=plain --tag palette-lab-ci .
      - run: python scripts/check_hosting.py --docker palette-lab-ci --report ci-results/docker.json
      - uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        if: always()
        with: {name: docker, path: ci-results/, if-no-files-found: warn}
```

These action SHAs were verified from their official repositories during the review. Pinning commits avoids silently following moving tags. No pull_request_target, secret access, artifact execution from another trust boundary or registry publication is needed. [GitHub secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use).

The fresh venv step runs once per job/cell and updates GITHUB_PATH for subsequent steps; it does not enable system-site-packages. The distribution verifier creates a second clean runtime venv so its build tools cannot mask undeclared application requirements. The proposed setup-node revision supports package-manager-cache:false; no package.json/npm cache is needed.

Watchdog and reporting requirements:

- Worker loads unittest from tests/ without adding the repository root when running installed tests. It uses TextTestRunner results to record testsRun, failures, errors, skips and duration.
- Record platform, architecture, exact Python micro version, NumPy/Pillow/package versions, pip freeze, node/Ruff versions where relevant and CI_COMMIT_SHA. For PR runs github.sha can be a merge-test commit; identify that as the tested SHA, not falsely as the PR head.
- Parent enforces 180 seconds for a suite. On POSIX launch it in a new session and terminate/kill only that process group. On Windows use a known spawned PID and bounded taskkill /PID <pid> /T /F if watchdog expiry requires killing the worker and descendants; never kill processes by a broad image name.
- Child-server helpers always stop/reap their own Popen in finally. The watchdog covers catastrophic fixture hangs that bypass these finalizers.
- Write logs to ci-results; on timeout preserve the last bounded stdout/stderr, return code and unfinished status. Missing worker counts are unknown, not zero successful tests.
- Runtime tests patch Remote.get to prohibit real acquisition and record any attempt, while FakeRemote fixtures and loopback HTTP remain allowed. A swallowed acquisition exception must still mark the run failed if the tracker records an attempt.
- CI job timeouts cap installation/build operations too. Optional live canaries have no required-check status.
- Mutable hosted-runner images and Python minor selectors do not provide byte-for-byte environmental identity. Record actual micro versions and image metadata; dependency/action pins plus fixtures support reproducible behavior, not an unqualified hermetic-build claim.

Docker protocol: run the built image detached with an ephemeral container name, PALETTE_HOST=0.0.0.0, explicit PORT=8765, PALETTE_DATA_DIR=/tmp/palette-ci-data, PALETTE_EXTERNAL_URL=https://lab.example.test and a public dummy password of at least 16 characters. Publish only to loopback with Docker's dynamically assigned host port; discover it using docker port. Query with Host: lab.example.test so application host checks match the configured HTTPS proxy identity, even though this private CI connection is plain HTTP. /health must return only status:ok, unauthenticated state must return 401, authenticated state must return 200 with an empty real corpus. Finally capture logs and docker stop the exact owned container with a five-second timeout; force-stop it if necessary. Do not prune Docker resources or delete directories. Runner disposal handles residual container/image artifacts.

Keep the Dockerfile unchanged. Its floating base image/dependency resolver are a recorded reproducibility limitation; record image ID/base digest and installed versions. A separate base-image pinning policy is better postponed than folded into this narrow verification PR without an actual successful image build.

Render static contract: parse YAML with PyYAML.safe_load and require exactly one service with type=web, name=scientific-palette-lab, runtime=docker, plan=0.5c-512mb, branch=main, healthCheckPath=/health and numInstances=1. Require disk name=research-corpus, mountPath=/var/data and sizeGB=1. Require exactly the four current env keys: PALETTE_HOST=0.0.0.0, PALETTE_DATA_DIR=/var/data, PALETTE_WEB_USERNAME=researcher, and PALETTE_WEB_PASSWORD with sync:false and no literal value. Confirm the data-dir matches the disk. PORT and RENDER_EXTERNAL_URL are supplied by hosting; do not invent tracked secret values or require an external URL placeholder. This proves syntax and agreement with the reviewed configuration, not Render-side deployability. The plan identifier is valid in the current provider documentation. [Render compute plans](https://render.com/docs/compute-plans), [Blueprint specification](https://render.com/docs/blueprint-spec).

## E. Compact scientific fixture design

Use one small JSON expectation file for interpreted scalar/projection results; construct raster fixtures deterministically in tests. Never snapshot full databases, image hashes, random UUIDs, timestamps, entire HTTP state or arbitrary current output.

| Contract | Fixture and exact expected behavior | Why it matters |
|---|---|---|
| RGB/Lab, ΔE76 | Existing white/red Lab tolerances; add black L≈0, identity ΔE=0, red/blue ΔE≈176.314039 within 1e-6 | Protect D65/sRGB conversion and existing metric; tolerance reflects floating arithmetic |
| Categorical raster | Existing solid known-color bars; assert HEX set, detected_count, method and semantic neutral policy | Solid interiors have authored truth; no interpolation/renderer snapshot needed |
| Neutral handling | Black/gray data shapes on white: omitted by default, included with include_neutrals; white remains background | Freeze the current heuristic, not a claim it is scientifically ideal |
| Alpha | Known 40×20 RGBA fixture in Task 1: red at alpha 128 over white becomes #FF7F7F; opaque blue preserved; transparent region omitted | Protect effective observed colors and current white compositing |
| Palette size | Known two/three/four colors; a 13-color fixture with max_colors=3 must report detected_count=13 and a truncation flag while returning three | Distinguish observed detection count from preview cap |
| Matching | Existing reversed categorical, ordered and role-aware assertions; add mismatched/empty palette infinity, symmetric distances and bottleneck example | No many-to-one/role/order regression or metric substitution |
| Ordered encodings | Sequential and diverging palette reversal changes matching; reviewed order remains in medoid/export | Ordered semantics do not become categorical sorting |
| Complete link | Existing blue chain whose adjacent distances pass but endpoints fail produces two families | No transitive single-link merge |
| Review/storage gates | Existing pending/excluded/unreviewed, stale revision, split bounds, re-extraction, DOI and manuscript tests | Keep current data/API/review behavior |
| Family medoid | Three distinct blues C0/D0/E0, duplicate C0 panels; D0 is representative under threshold 25 | Medoid over distinct variants, not a duplicate-weighted mean or popularity winner |
| Paper/panel counts | Eight explicit panel rows over five papers, described below | Compact hand-counted denominators/membership/journal/year semantics |
| Bootstrap | Same fixed paper IDs, seed 2021, 100 draws; expected projected intervals below; repeated call also identical | Catch an accidental RNG, panel resampling or seed change |
| Recommendations | Two observed three-color families and current references, exact scores/order below | Preserve measured CVD, contrast, origin and score semantics |
| Reference palettes | Exact Okabe–Ito/Tol arrays and current role-reference assignments | Reference values cannot drift during infrastructure work |
| HTTP exports | A tiny actual Store with reviewed categorical/ordered/role panels; CSV DictReader and JSON projections agree with families | Preserve public export fields, quoted scope JSON and source/version semantics |

For the preview-cap example, use equal-area opaque bands of #FF0000, #00FF00, #0000FF, #FFFF00, #FF00FF, #00FFFF, #800000, #008000, #000080, #808000, #800080, #008080 and #FF8000. Verify pairwise ΔE76 >1 as a fixture precondition, use threshold=1 and max_colors=3, and check detected_count=13 separately. No font/antialiasing/white space is involved. This fixed high-chroma list prevents random colors from accidentally merging or background pixels from adding a palette color.

Eight-row statistics fixture:

- paper a, Nature/2024: three separate #0000C0 panels and one #FF0000 panel;
- paper b, Cell/2023: one #0000D0 panel;
- paper c, Science/2025: one #0000E0 panel;
- paper d, Science/2025: one #FF0000 panel;
- paper e, Nature/2024: one two-color #0072B2/#E69F00 panel.

All are explicit reviewed/included/published data/categorical panels with fixed IDs. Under threshold=25:

| Family | Representative | Papers/panels | Paper/panel denominator | Prevalence | Variants | Bootstrap 100 |
|---|---|---|---|---:|---:|---|
| Two-color | #0072B2/#E69F00 | 1 / 1 | 1 / 1 | 1.0 | 1 | [1.0,1.0] |
| Blue | #0000D0 | 3 / 5 | 4 / 7 | 0.75 | 3 | [0.25,1.0] |
| Red | #FF0000 | 2 / 2 | 4 / 7 | 0.5 | 1 | [0.0,1.0] |

Total analyzed papers/panels = 5/8. Blue by_journal = Nature:3, Cell:1, Science:1; by_year = 2024:3, 2023:1, 2025:1. These are panel counts. Paper a uses two families, so within the one-color bucket prevalence sums to 1.25; this is existing valid semantics, not a bug to “normalize.” Assert family members using fixed panel IDs, medoid colors and rank/projections; avoid storing UUID-bearing sources.

Recommendation fixture: one paper uses [#0072B2,#E69F00,#009E73], one uses [#FF0000,#FF0101,#0000FF]. Both are reviewed categorical three-color families; prevalence is 0.5 each.

| Default white-background order | Score | Origin |
|---|---:|---|
| Observed first palette | 0.5197 | observed |
| Observed collision palette | 0.4083 | observed |
| Okabe–Ito reference subset | 0.1947 | reference |
| Paul Tol bright reference subset | 0.1841 | reference |

For the first palette, existing accessibility gives min_simulated_delta_e=16.97 and background contrasts [5.19,2.25,3.42]. Independently compute round(0.55×0.5 + 0.30×(16.97/30) + 0.15×(2.25/4.5),4)=0.5197. The identical reference has prevalence=None, contributes zero popularity and receives -0.05, yielding 0.1947. This arithmetic explains the golden values rather than blindly copying them.

With black background, scores become 0.5797/0.3566/0.2547/0.2298 in the same order. With cvd_filter=True, the collision palette disappears; qualifying references remain. Locking #0072B2 retains only its observed family and Okabe–Ito subset. include_references=False returns only observed families. Add a sequential case: quality contribution remains 0.5 and the categorical collision filter does not remove continuous neighbors. Flowchart separation uses fill/decision/group colors, while background contrast still follows the current full palette. Low background contrast warns and changes the score; do not introduce a new exclusion.

Pin current simulated HEX arrays for the small reference fixture as compatibility evidence, while retaining approximate/accessibility disclaimers. Assert scores at four-decimal output precision, HEX/roles/counts exactly, and Lab/ΔE values with justified numerical tolerance. Never change expectations merely to make a new algorithm pass.

## F. Packaging and installed-package validation

Current setuptools package-data pattern web/* covers the three existing flat files index.html, app.js and style.css. There are no current nested schema/migration resources to implement. Keep this pattern until actual current-resource verification shows otherwise.

Create tests/test_package.py with resource, metadata and existing-schema checks:

- importlib.resources.files("palette_lab").joinpath("web", name).read_bytes() for each current asset; assert nonempty and compare to wheel/source resource bytes in the distribution verifier.
- Assert __version__ and importlib.metadata.version("scientific-palette-lab") agree at 0.1.0 and the palette-lab console entry point resolves to palette_lab.__main__:main.
- Fresh Store has exactly papers/figures/panels/reviews/runs; check representative column lists and current foreign-key/WAL behavior, not a fragile hash of formatted CREATE statements.
- Static resource test does not make live requests. Installed server tests prove resources actually serve.

Build using python -m build --no-isolation after explicitly installing the pinned backend/build requirements. The default build path produces an sdist and builds a wheel from it, exercising sdist completeness. Inspect both archives read-only with zipfile/tarfile; do not extract arbitrary archives into a user directory. Confirm all tracked package Python modules, all three web assets and correct distribution metadata/entry point. Package tests/scripts/fixtures need not be shipped as runtime package data. [PyPA build](https://build.pypa.io/en/stable/).

Distribution verifier sequence:

1. Identify exactly one current-version wheel and one sdist; extra/stale artifacts fail with filenames, not arbitrary “first match.”
2. Create an owned venv with with_pip=True and a separate working/data directory outside the checkout. Runtime dependencies are installed with CI constraints; no dev extra or inherited system-site-packages.
3. Install the exact built wheel with --no-deps after its declared runtime requirements are installed; run pip check and record pip freeze. This ensures the clean runtime is explicit. Audit distribution Requires-Dist entries separately.
4. Run the venv Python with -I and verify palette_lab.__file__ points inside this venv and outside the checkout. Remove PYTHONPATH/PYTHONHOME for child processes. Adding only the repository's tests directory for discovery must not add its package root.
5. Read installed resources and compare bytes, invoke python -m palette_lab --help and the installed palette-lab executable --help with timeout=10.
6. Run demo into an explicit owned directory with timeout=30; verify 12 demo records and zero real papers. Start serve --port 0 --host 127.0.0.1 using -I -X utf8 -u; use the same file-log helper and health/state/static checks.
7. Run the full test suite against the wheel from the external cwd, with the same 180-second watchdog. StartupTests must use a caller-supplied cwd so this mode cannot silently switch back to PROJECT.
8. Record build/archive/install/resource/help/demo/server/unit-suite statuses independently; finally stop/reap owned processes and close all handles. Preserve failure logs before test-owned CI cleanup.

Do not use an editable installation for the installed-package acceptance check. Do not claim the current historical wheel-build note proves these checks. Windows console scripts live under Scripts; POSIX under bin—resolve the venv path explicitly rather than assuming a .venv/bin layout everywhere.

## G. Cross-platform subprocess and timeout strategy

Choose **file-backed stdout/stderr plus bounded polling of the existing startup announcement**, followed by HTTP checks. This is the smallest robust approach for this server because port 0 and a flushed URL are already implemented.

| Alternative | Assessment |
|---|---|
| select on pipes | Reject: unsupported on Windows; readline can still block after partial readiness |
| communicate(timeout) alone | Good for commands that finish, but cannot discover readiness while a long-lived server remains running |
| One reader thread plus queue | Portable, but requires EOF/queue limits and careful ownership; stderr needs draining too |
| Two reader threads/queues | Robust with proper shutdown, more moving parts than needed here |
| HTTP polling with a pre-selected fixed/free port | Reintroduces bind/close/start races or port collisions |
| File logs + port-0 announcement + HTTP | Selected: no pipe buffers/readers, no bind race, both diagnostics retained |

Test helper behavior:

```python
deadline = time.monotonic() + 30
while True:
    with stdout_path.open("rb") as log:
        text = log.read(65536).decode("utf-8", errors="replace")
    match = re.search(
        r"^Scientific Palette Lab → (http://127\.0\.0\.1:\d+)\r?\n",
        text, re.MULTILINE,
    )
    if match:
        url = match.group(1)
        break
    if process.poll() is not None:
        raise AssertionError(diagnostics(process, stdout_path, stderr_path))
    if time.monotonic() >= deadline:
        raise AssertionError(diagnostics(process, stdout_path, stderr_path))
    time.sleep(0.05)
```

diagnostics reads bounded log tails, includes return code/deadline/data directory/last URL or HTTP exception, and is a concrete test-only helper in tests/support.py. Logs are two owned regular files; use separate parent read handles so child/parent file offsets do not interfere. Force UTF-8 through Python -X utf8 and -u; do not rely on Windows' redirected-output encoding for the arrow character. Match only a complete newline-terminated startup line and validate the returned host/port before requesting it.

After obtaining URL, poll /health until the same startup deadline with per-request timeout=min(1, remaining budget); early exit aborts immediately. Require status 200 and exact {"status":"ok"}, then query one minimal state endpoint with timeout=2. Use a no-proxy loopback opener so inherited proxy settings do not send localhost checks externally. Do not create a new health/startup API.

| Operation | Bound |
|---|---:|
| CLI help/error command | 10 seconds |
| Demo initialization | 30 seconds |
| Server URL plus health readiness | 30 seconds total |
| Individual health connect/read attempt | At most 1 second, within remaining readiness budget |
| Minimal state/static/export HTTP operation | 2–5 seconds; suite watchdog remains outer bound |
| Normal server subprocess termination | wait 5 seconds |
| Forced kill/reap | wait 5 seconds |
| Hosting fixture shutdown thread and serve thread join | 5 seconds each; assert terminated |
| Node export process / VM synchronous execution | 10 seconds / 1 second |
| Full unittest worker | 180 seconds |
| Installed dependency/build subcommand inside verifier | 120 seconds; CI job also bounded |
| Docker readiness / Docker stop | 30 seconds / 5 seconds |
| CI job | 10–15 minutes including dependency/build infrastructure |

For in-process hosting tests, initiate shutdown from a separate thread, join it with a timeout, then server_close and join the serve thread. Fail explicitly if either remains alive; do not silently accept a timed-out join. Register cleanup after server construction, account for thread-start failure, and avoid shutdown on a never-running serve loop. A catastrophic fixture hang is caught by the suite watchdog.

Terminate/kill in a subprocess smoke test proves bounded resource cleanup, not application-level graceful exit code 0. Windows terminate uses TerminateProcess; POSIX terminate sends SIGTERM. The current CLI has no portable shutdown endpoint. Keep that behavior; in-process tests use shutdown, and do not add a production shutdown API solely for CI. [Python subprocess](https://docs.python.org/3/library/subprocess.html).

## H. Socket/bind error strategy

Keep the existing EADDRINUSE recovery text, plus a portable python -m invocation. Add a small testable _startup_diagnostic(exc, host, port) -> str | None helper in __main__.py, used only by the existing serve OSError handler:

```python
except OSError as exc:
    message = _startup_diagnostic(exc, args.host, args.port)
    if message is None:
        raise
    parser.exit(1, message)
```

The helper recognizes explicit categories:

| Category | POSIX errno | Windows winerror | Diagnostic and compatibility |
|---|---|---|---|
| Address already used | EADDRINUSE (number differs by OS) | 10048 | Existing actionable conflict message, same exit 1; stop own service or choose another port |
| Access denied | EACCES / EPERM | 10013 | Access-denied wording, original errno/winerror; mention exclusive listener/reserved port/permissions as possible causes; suggest another permitted port or checking policy |
| Requested address unavailable | EADDRNOTAVAIL | 10049 | State address unavailable and include actual host/port/error; choose an address present on this machine |
| Unexpected error | Other | Other, including 10038 at runtime | Preserve exception/traceback; do not disguise programmer/resource failures as port conflicts |

Use getattr(exc,"winerror",None) and symbolic errno names; do not assume Linux/macOS errno numbers equal Windows values. Preserve the original exception text/code. Never offer “run as administrator” as the default repair, never stop an existing process automatically, and never try to prove occupancy by connecting to unrelated services.

For 10013, proposed wording is: “Cannot start the web application at <host>:<port>: access denied (<original OS error>). Windows may deny binding because an exclusive listener or reserved port exists, or because of system policy. This error does not identify the cause by itself. Choose another permitted port or inspect the endpoint's reservation/permissions.” This is a template for formatting actual arguments, not a claim that every access-denied case is a collision.

Preserve Store creation before serve, default host/port, demo initialization, ValueError handling and unknown-error behavior. Do not change app.serve, HTTP server class or socket options. app.py's only planned edit is the unused import in Task 3.

## I. File-by-file change list

Repository-relative paths below are proposed paths in the future implementation branch. Source line numbers refer to the reviewed main SHA, not lines after editing.

### Create

| File | Responsibility / affected symbols | Associated verification |
|---|---|---|
| .github/workflows/ci.yml | Required matrix, quality, distribution and Docker jobs | Every named job/cell green; no live-source steps |
| ci/constraints.txt | Exact CI tool/runtime pins with Python markers | Cold installs, pip check, recorded versions |
| ci/constraints-minimum.txt | Python 3.10 declared-floor runtime profile | Minimum-runtime suite and demo |
| tests/support.py | running_server, wait_for_url, diagnostics, stop_process; owned fixtures | Startup success/error/timeout/reap cases |
| tests/test_baseline.py | BaselineTests and fixed Rows/row helpers | Interpretable extraction/statistics/recommendation assertions |
| tests/fixtures/v01-scientific.json | Small expected scalar/projection values and fixture rationale | No UUID/time/image blobs; exact counts/roles/order |
| tests/test_exports.py | ExportTests: actual browser generator and HTTP JSON/CSV | ast.parse/compile, json.loads, csv.DictReader; ordered/role contracts |
| tests/export_harness.cjs | Evaluate actual downloadCode source slice in Node VM | Four existing branches; no copied generator or frontend build |
| tests/test_package.py | PackageTests: metadata/resources/current schema | Flat runtime assets, console entry point, five existing tables |
| scripts/run_tests.py | Parent watchdog, unittest worker, offline-acquisition guard, dynamic JSON | Failure/no-tests/timeout cases; process tree reaped |
| scripts/verify_distribution.py | Archive and clean installed-wheel verification | Wheel/sdist/resource/help/demo/full installed-suite smoke |
| scripts/check_hosting.py | Render static assertions and owned Docker smoke | Parsed expected fields; health/auth, logs and bounded stop |
| docs/DEVELOPMENT.md | Exact commands, supported profiles, Ruff scope and evidence interpretation | Documentation command smoke; current reports linked |

### Modify, narrowly

| File / current location | Required change | Compatibility impact and test |
|---|---|---|
| __main__.py main lines 35–49 | Recognized error helper/handler; portable recovery command alongside existing conflict recovery | stderr becomes accurate for identified portability errors; exit 1 preserved; mock and real-listener tests |
| app.py line 24 | Remove unused eligible_panels import only | No route/body/API behavior; full baseline/security/export suite |
| pyproject.toml | Pillow >=10.1, optional dev tools, explicit Ruff config | Correct install floor, no new base runtime dependency; minimum/install matrix |
| tests/test_cli.py StartupTests | File-log helper; explicit loopback/port0/environment/cwd; correct OS conflict assertions | Test-only; both existing tests retained |
| tests/test_hosting.py setUp/start_server/stop_server/tearDown | Register immediate cleanup; bound shutdown/join; use shared owned-directory fixture | Existing HTTP/security expectations unchanged; no orphan threads/connections |
| tests/test_hosting.py authentication/path tests | Add authenticated traversal rejection and style.css authentication; malformed credentials at HTTP boundary | Protect existing behavior only; confirmed new defect requires separate scope decision |
| tests/test_pipeline.py imports/setUp/tearDown and duplicate-upload test | Remove four unused imports; immediate cleanup; verify one asset after duplicate upload in ordinary CI | No science assertion rewrite; real cleanup only within owned test root |
| README.md | Development link, portable Windows commands, current CI evidence pointer | No scientific/hosting claims rewritten as new features |
| VALIDATION.md | Mark historic reports; link generated current CI artifacts and distinguish benchmark validation | No hand-maintained current totals; old evidence remains identifiable |

StartupTests uses PALETTE_TEST_CWD only as a test-runner override: default PROJECT for source-mode tests, an external owned directory for installed-mode tests. Its helper receives cwd explicitly. All child processes receive an explicit --data-dir. ExportTests locates app.js through the imported palette_lab package's resources and passes that actual path to the Node harness; installed-mode tests must therefore exercise installed JavaScript, not the checkout copy.

### Explicitly leave unchanged

- colors.py, statistics.py and recommend.py: all algorithms, constants, rounding, weights, references, CVD calculations, grouping and estimands.
- store.py: every table/column/constraint/transaction and existing review/eligibility/deduplication semantics.
- corpus.py, config.py, figures.py, classify.py and demo.py: scope, acquisition/version policy, heuristics and demo rendering.
- app.py:Application, handler_for and serve bodies; only its unused import is removed.
- palette_lab/web/app.js, index.html and style.css: frontend behavior/styles/export implementation.
- run.sh, Dockerfile, render.yaml, .dockerignore: keep current production launch/deployment configuration; validate it.
- __init__.py/version, reference palettes, code-license metadata, data files and current API responses.
- PR #1's original verification snapshot: it records the old main audit, not this future implementation's CI.

No file removal is needed. No migrations, history tables, new datasets or sampling code are permitted.

## J. Branch workflow and focused commit sequence

This is a proposed future workflow, not an action performed by this review:

1. The owner reviews this plan and separately authorizes implementation. Finalize/merge the documentation PR #1 only when authorized.
2. Fetch current origin/main, verify a clean/suitable checkout and read its applicable AGENTS.md. Branch from that updated main, not from the docs branch. Proposed exact name: engineering/pr01-baseline-ci.
3. Confirm that application source still matches the reviewed baseline; investigate any intervening scientific changes before using these fixtures as expectations.
4. Implement only the task/commit sequence below. Each commit gets its focused verification before pushing.
5. Open a new implementation pull request with §L as its checklist and explicit before/after fixture evidence. Do not add implementation commits to documentation PR #1.
6. Wait for every required job/cell; inspect failure logs rather than waiving portability failures.
7. Review production diffs against the unchanged-files list. Confirm that diagnostics/import/dependency metadata are the only application-side edits.
8. Merge only after the owner authorizes merge and the complete baseline is green. Start PR #02 from the merged baseline afterward.

| Commit | Title | Dependency and verification |
|---|---|---|
| 1 | test: freeze v0.1 scientific and export contracts | Task 1; reviewed main first; new fixtures pass without production fixes |
| 2 | fix: report socket failures accurately and make startup tests portable | Task 2; add failing code-category tests first, then diagnostics/helper; all original 35 tests pass |
| 3 | chore: adopt scoped lint and correct Pillow compatibility metadata | Task 3; six non-style Ruff findings removed; baseline still identical; declared-floor demo |
| 4 | build: verify distributions and isolated installed-package startup | Watchdog/package/Render-Docker scripts and package tests; build both artifacts and run clean installed suite |
| 5 | ci: add required Python Windows and container checks | Pinned constraints and workflow; every matrix/distribution/quality/Docker cell passes |
| 6 | docs: document reproducible development and current verification evidence | README/DEVELOPMENT/VALIDATION; no static current test count; scope/non-regression review |

The watchdog can land with commit 4 and be used by subsequent CI. New HTTP export tests may depend on the portable helper in commit 2; if they do, commit 1 contains the pure generator/scientific tests and commit 2 adds those HTTP cases. Do not temporarily skip an important failing test and call the baseline green.

Before each production edit, run the existing scientific tests and the new interpretable fixtures. After each edit, repeat those checks. Once passing, do not expand to unrelated refactors or future infrastructure.

## K. Risks, mitigations and limits

| Risk | Mitigation / decision rule |
|---|---|
| Windows 10013 misreported as collision | Distinct access-denied category with original codes; mocked conflict/permission/address/unknown cases; no socket-option production change |
| Port availability race | Let the actual server bind port 0; parse its flushed real URL; never pre-bind then release a “free” port |
| Incorrect listener sharing in occupied fixture | Exclusive test listener on Windows when available; connect to original listener after failed child startup; do not assume EADDRINUSE only |
| Partial output or pipe deadlock | Regular log files, complete newline matching, capped reads, process.poll and monotonic deadlines; no pipe readline |
| Child exits before readiness | Immediate return-code/log failure; no full-deadline wait after known exit |
| Inherited user/CI hosting settings or proxy | Sanitize only documented PALETTE/PORT/external-url variables; explicit data-dir/loopback; no-proxy opener |
| UTF-8 arrow fails under Windows redirection | -X utf8 -u; explicit UTF-8 log decoding |
| Orphan process after test/suite failure | Helper finally terminate/kill/reap; outer watchdog terminates only owned worker process tree |
| In-process server teardown hangs | Immediate addCleanup; bounded shutdown/serve-thread joins; outer suite deadline catches catastrophic hangs |
| Temporary-file ACL difference | Explicit accessible test-owned root; record creation errors; no production chmod/admin workaround; local retained audit distinct from normal CI |
| Deletion reaches user/repository data | Dedicated test root and explicit --data-dir; no bulk cleanup command; local deletion permission rules remain; no production cleanup additions |
| Wheel check imports checkout | External cwd, -I, sanitized Python path, assert module path inside clean venv; tests directory only for discovery |
| Missing package data | Compare all current Python modules/static bytes in wheel and sdist; exercise HTTP-served assets from installed package |
| Dependency resolver hides incompatibility | Pinned profiles, no isolated unconstrained backend, pip check, declared-floor cell, base-only/clean-venv checks |
| Golden fixtures freeze accidental UUID/time order | Fixed test IDs, deterministic projections and explained scalar/count semantics; no whole-state snapshots |
| Float/library differences create brittle tests | Exact HEX/counts/rounded public scores; justified Lab/ΔE tolerance; report exact NumPy/Pillow versions; investigate discrepancies, never auto-update goldens |
| CI claims prove scientific extraction accuracy | Clearly separate engineering compatibility fixtures from a real-panel scientific benchmark |
| Ruff creates unrelated churn | Measured one-file E701/E702 exception; five unused-import removals; named formatter scope; no format-all or F-rule suppression |
| Node test quietly misses generator changes | Read actual package resource; strict function-boundary markers; generated AST/JSON assertions; fail rather than skip |
| Ordinary CI hits live services | Offline FakeRemote plus guarded Remote.get; loopback tests remain allowed; no collect CLI/source canary steps |
| Docker host/origin check blocks CI probe | Public dummy HTTPS external identity plus matching Host header; only loopback-published host port; health/authenticated state tests |
| Container build changes base/deps silently | Log base/image IDs and installed versions; retain Dockerfile for this scope; disclose non-hermetic image limitation |
| CI status is incomplete or canceled | Stable required checks for every cell; artifacts even on failure; timeout/canceled/unrun is not pass |
| New security/path test reveals unrelated bug | Reproduce, explain and seek scope decision before changing security semantics; do not expand silently |

No macOS job is required here. Symbolic errno tests cover its error categories, but this review and proposed Linux/Windows matrix do not prove macOS end-to-end support.

## L. Final acceptance checklist for the implementation PR

Copy these unchecked items into the future GitHub implementation PR; check each only with actual evidence:

- [ ] Reviewed base SHA, implementation head SHA and actual tested CI SHA are identified; PR #01 is separate from documentation PR #1.
- [ ] All 35 original tests remain present and pass; any new count comes from the runner report.
- [ ] Linux full suite passes on Python 3.10, 3.11, 3.12 and 3.13.
- [ ] Windows Python 3.12 full suite passes, including both original startup cases.
- [ ] Declared-floor Python 3.10 runtime profile passes, including demo/font compatibility.
- [ ] Occupied-port, permission-denied and unavailable-address diagnostics remain distinct; unknown errors are not relabeled.
- [ ] The original occupied listener survives failed application startup; no process is automatically stopped.
- [ ] Startup uses the server's own OS-assigned port and bounded file-log/health polling; no select on subprocess pipes remains.
- [ ] subprocess/HTTP/shutdown/build operations have explicit deadlines and useful stdout/stderr/return-code diagnostics.
- [ ] Early-exit, no-announcement, timeout and forced-reap cases are tested; no orphan process/thread survives normal test failure.
- [ ] Interpretable raster/alpha/neutral/size/Lab/ΔE76 fixtures pass without algorithm edits.
- [ ] Categorical order invariance, sequential/diverging order, one-to-one and role-aware matching are unchanged.
- [ ] Paper votes, panel counts, count-specific denominators, complete-link membership, medoids and panel-based journal/year fields match the stated fixtures.
- [ ] Manuscript opt-in, real/demo separation, review/eligibility/split/deduplication/re-extraction effects remain unchanged.
- [ ] Seed-2021 paper bootstrap and explicit expected intervals are unchanged.
- [ ] 55/30/15 scores, reference penalty/arrays, origins, locked color, background warnings and CVD filtering/order are unchanged.
- [ ] node --check passes; categorical/sequential/diverging generated Python parses/compiles and preserves ordered HEX values.
- [ ] Flowchart generated JSON preserves kind/origin/HEX/roles; HTTP CSV/JSON exports retain current fields and scope semantics.
- [ ] Ruff lint passes across adopted code; every non-default ignore is documented and confined to the measured legacy test file.
- [ ] Ruff format --check passes for the named adopted scope; no unrelated repository-wide formatting diff.
- [ ] Wheel and sdist build successfully; the wheel-from-sdist path and archive contents are verified.
- [ ] Wheel installs in a clean runtime venv with no dev/scientific undeclared dependency; pip check passes.
- [ ] Installed import comes from that venv outside checkout; console/module help, three static assets, demo, health and minimal state pass.
- [ ] The same full tests run successfully against the installed wheel on Linux/Windows, without checkout import masking.
- [ ] Normal tests make no live acquisition requests; source parser fixtures are deterministic.
- [ ] Authentication for UI/API/exports/static/assets, malformed credentials, host/origin checks, traversal boundaries and external-bind requirements pass.
- [ ] Test-owned directories/assets/subprocesses are isolated; actual CI cleanup is verified, and retained local runs are labeled as not cleanup verification.
- [ ] render.yaml parses and satisfies the existing single-Docker-service/disk/env/secret/health expectations.
- [ ] Docker build and local health/auth smoke pass; exact owned container is stopped and logs are retained.
- [ ] CI prints versions/OS/commit, produces dynamic result counts and artifacts, and fails on incomplete/timeout/unrun checks.
- [ ] VALIDATION separates historical audit, current engineering CI and scientific benchmark evidence; no stale manual current totals.
- [ ] No database schema migration, future corpus/history tables or PR #02 changes occur.
- [ ] No scientific algorithm/constants/reference/API/review/data-model behavior changes unintentionally.
- [ ] No frontend/backend framework migration, new runtime model service, licensing decision or cloud deployment occurs.
- [ ] Production diff is limited to CLI diagnostics, the one unused import and dependency metadata; all scientifically relevant file bodies remain unchanged.
- [ ] Every required check is green on the reviewed implementation head before authorized merge and before PR #02 starts.

## Final recommendation — explicit answers

**1. Is PR #01 appropriately scoped?** Yes. Portability, baseline contracts, CI and distribution verification form one coherent prerequisite. The corrected Pillow minimum belongs here because it fixes an existing package-install compatibility defect without changing the implemented behavior.

**2. What should be postponed?** Full-repository formatting/lint expansion, additional metadata/classifiers/license choice, generalized resource architecture, live canaries, base-image pinning policy without a successful build, and all future scientific/database/application features. No new shutdown API, server framework or test framework is needed.

**3. What is missing before PR #02?** The current baseline is not green. Require both accurately fixed Windows cases, cross-platform and declared-floor checks, real installed-wheel/resource proof, compact scientific/export fixtures, bounded cleanup/diagnostics, and current CI evidence. Do not treat old VALIDATION claims or documentation checks as substitutes.

**4. Can PR #01 avoid changing scientific outputs?** Yes. Keep scientific/storage/frontend/demo bodies unchanged; add tests around them. CLI stderr and dependency metadata are the intentional compatibility changes. If any scientific fixture differs, investigate before proceeding; a new algorithm or silent golden update is outside authorization.

**5. Minimum necessary changes for a genuinely green, reproducible v0.1 baseline:** portable bounded test support; precise recognized OS diagnostics and matching test expectations; compact scientific/export regression cases; corrected Pillow floor and narrow Ruff adoption; pinned/recorded Linux and Windows CI; wheel/sdist plus clean installed-package checks; static hosting and local Docker verification; dynamic evidence documentation. No PR #02 or new scientific pipeline work is necessary.

Implementation is ready to be reviewed as this plan. It remains unauthorized until the user gives that instruction; this review does not merge PR #1, create the implementation branch or publish anything to GitHub.

# Task 1 report — scientific and actual JavaScript export contracts

Status: complete for the assigned scientific/JavaScript scope. Actual HTTP CSV/JSON export assertions are deferred to Tasks 2/4 shared server support as instructed. No production code or pre-existing test was changed by this task.

## Changed files

- `source/tests/test_baseline.py`: 15 unittest contracts. Test-only `Rows.panels(dataset)` exposes explicit immutable `MappingProxyType` panel/color dictionaries and tuples. Covers D65/sRGB white/red/black, identity and red-blue ΔE76, authored two/three/four-color raster interiors, neutral/background policy, deterministic alpha, 13-color detection versus preview cap, matching/order/roles/infinite distance/bottleneck symmetry, complete link, reviewed sequential/diverging order, distinct-variant medoid, fixed members/ranks/journal/year counts/denominators, deterministic paper bootstrap, approximate simulations/disclaimer, 55/30/15 scoring/reference penalty, exact white/black scores/order/counts/roles/origins, CVD/lock/reference constraints, sequential quality, flowchart fill separation/full-palette background contrast, and reference values/roles.
- `source/tests/fixtures/v01-scientific.json`: one compact authored expectation file with written rationales for scientific floating tolerance, solid raster truth, alpha weights, hand-counted statistics/medoid, bootstrap projections, recommendation arithmetic and compatibility simulation/reference arrays. Excludes UUIDs, source snapshots, timestamps, databases and image hashes.
- `source/tests/test_exports.py`: 5 unittest tests with Node subprocess timeout 10 seconds and JSON content/filename envelope. AST parse/compile checks categorical cycler assignment/imports, sequential/diverging `LinearSegmentedColormap.from_list` assignment/import, and exact reviewed order including recommendation palette-type fallback. Asserts demo/reference provenance, JSON-decodes flowcharts with exact colors/roles/origins, and verifies that missing/duplicate/reordered markers fail clearly. Node prerequisite is a hard setup error, never a CI skip. Normal portable tests use TemporaryDirectory/addCleanup.
- `source/tests/export_harness.cjs`: Node built-in fs/path/vm only. Reads actual `palette_lab/web/app.js`, requires exactly one start/end marker in the right order, evaluates the actual `downloadCode` source slice with timeout 1000 milliseconds, supplies tiny Blob/URL/document/setTimeout stubs, verifies click/revoke, captures content/filename, and emits a JSON envelope. No copied export generator, DOM/npm dependency, network call or frontend restructuring.

## Verification

Bundled runtime: Windows Python 3.12.14; Node v24.19.0. Local runs used the external retained audit runner, not retained-file logic in committed tests. Actual cleanup remains unverified; all accessible audit artifacts are retained.

PowerShell invocation (profile disabled by tool `login=false`):

```powershell
$env:PATH='C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;' + $env:PATH
& 'C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B `
  'F:\codex\Project Plan\pr01-implementation\run_retained_tests.py' `
  --source 'F:\codex\Project Plan\pr01-implementation\source' `
  --pattern test_baseline.py `
  --report 'F:\codex\Project Plan\pr01-implementation\artifacts\task-1-baseline-pass.json'
```

Same command with the following pattern/report pairs:

| Pattern | Report | Result |
|---|---|---|
| `test_baseline.py` | `artifacts/task-1-baseline-pass.json` | 15/15 pass, 0 skipped; scientific gate passed before other agents began production edits |
| `test_exports.py` | `artifacts/task-1-test_exports.json` | 5/5 pass, 0 skipped |
| `test_pipeline.py` | `artifacts/task-1-test_pipeline.json` | Existing 27/27 pass, 0 skipped |
| `test_hosting.py` | `artifacts/task-1-test_hosting.json` | Existing 6/6 pass, 0 skipped |

Portable documented invocation is `python -B -m unittest discover -s tests -p test_baseline.py -v` and similarly `test_exports.py` with Node on PATH. Locally, the retained runner performs the equivalent discovery while replacing cleanup outside the source tree. All intended retained verification passed: 53 tests total across these four runs.

Additional prerequisite check loaded ExportTests, patched `test_exports.shutil.which` to return `None`, ran the unittest class through TestResult, and asserted exactly one setup error with `ExportTests require Node.js on PATH`, zero tests run and no skip. Evidence: `artifacts/task-1-node-prerequisite-confirmed.txt`.

The initial scientific fixture construction run had one authored expectation mistake: sequential collision-palette white contrast was assumed capped at 4.5. The existing code reports `[4.0, 3.99, 8.59]`, so the documented baseline formula gives `round(.55 + .30*.5 + .15*(3.99/4.5),4) = .833`, not .85. Corrected the test rationale/arithmetic without modifying production code or changing any approved golden score. Initial evidence retained at `artifacts/task-1-baseline.json`.

## Concerns and limitations

- HTTP CSV/JSON assertions remain Task 2/4 work, not verified by this task. Preserve the tiny reviewed categorical/ordered/role panel scope and assert CSV DictReader/JSON projections, quoted scope JSON and source/version fields there.
- Known CLI baseline failures are recorded separately by the parent/Task 2; Task 1 did not modify or rerun CLI tests.
- Only bundled Windows Python 3.12 was run here; Linux/Python 3.10–3.13 and ordinary filesystem cleanup await CI/authorized execution. Scientific behavior checks passed before production edits; cleanup is explicitly unverified.
- A failed attempt to test absent Node using an empty PATH and ordinary unittest discovery bypassed the retained runner. The bundled runtime still resolved Node, and protected `C:\Users\Lenovo\AppData\Local\Temp\tmprmz7lquu` writes/cleanup were denied, causing marker-test PermissionErrors. No deletion succeeded. This ineffective negative-check log is retained as `artifacts/task-1-node-prerequisite.txt`; it is not a product test regression or passing prerequisite evidence. The later mocked prerequisite check avoids file creation/cleanup and succeeds. No more ordinary tempfile runs were made.
- Tests deliberately pin current approximate ΔE76/full-dichromacy compatibility output and current neutral heuristic. They do not certify accessibility or justify a metric/algorithm substitution.

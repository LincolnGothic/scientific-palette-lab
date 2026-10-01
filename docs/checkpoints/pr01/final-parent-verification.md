# Parent verification of the frozen final fix

Frozen source: scripts/verify_distribution.py, scripts/run_tests.py, tests/test_package.py, tests/support.py and tests/test_cli.py against local e55b802e1e212dcf09716f452005b73526d5172d. No source edits were made between these runs.

- Retained source full suite: final-source-suite.json, 88/88, zero failures/errors/skips; final-source.stderr.log reports 26.976s.
- Retained isolated non-editable audit install: final-installed-suite.json, 88/88, zero failures/errors/skips; final-installed.stderr.log reports 26.821s. This is the existing source-audit environment and includes build bootstrap packages, so it is distinguished from the clean wheel environment below.
- Retained clean installed-wheel full suite: final-clean-wheel-suite.json, 88/88, zero failures/errors/skips. Reused unchanged wheel/runtime from task-4-fix-1-installed.worker.json. The helper uses -I and asserts installed package origin under sys.prefix and outside checkout; sets test_exports.APP_JS to the installed resource. Runtime package files did not change in this final fix, so no local rebuild was needed. See final-clean-wheel.stderr.log for full output.
- Windows covering suite: windows-ownership-green.json, 9/9, zero failures/errors/skips. Previous one-off test assertion rendering failure remains archived separately.
- Native owned-tree probe: five fixtures, all exact PID tree commands return0, both logs rename immediately; artifacts/windows-tree-owned-b4cfdae8726f412c9046a2f09e60d954/evidence.json.
- Root fresh Ruff full lint: passed. Scoped formatting: all9 files already formatted. Node syntax: passed. Executables are existing Ruff0.13.3 and local Node24.19.0; CI must exercise Node22.

Tests retained all temporary files and relocated one exact test-owned unlink target to its audit archive in each full run. No physical deletion/cleanup is established locally. Ordinary hosted cleanup, fresh builds/distributions, all supported/minimum profiles, and real Docker on the corrected head remain the hosted acceptance gates. This verification does not establish scientific extraction accuracy or representative corpus quality.

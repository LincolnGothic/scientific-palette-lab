# PR01 checkpoint for another computer

This is a draft progress checkpoint for `engineering/pr01-baseline-ci`. Continue from this branch; leave `main` and [documentation PR #1](https://github.com/LincolnGothic/scientific-palette-lab/pull/1) unmerged. The user authorized publishing this checkpoint so the work can continue on another device.

## Resume

```bash
git clone --branch engineering/pr01-baseline-ci https://github.com/LincolnGothic/scientific-palette-lab.git
cd scientific-palette-lab
git status --short
git rev-parse HEAD
```

Read the [approved implementation plan](plans/2026-09-30-pr01-baseline-portable-ci.md), [development commands](DEVELOPMENT.md), [progress ledger](checkpoints/pr01/progress.md), and [final branch review](checkpoints/pr01/final-branch-review.md). Archived reports contain paths from the previous Windows computer; use the repository-relative commands in the development guide on the new computer. Rebuild a diff from base `192abce8f86777911df0e1b4d62340c2a19e92f5` instead of relying on an old local path.

Suggested prompt for the new Codex chat:

> Continue PR01 from this branch and its draft PR. Read docs/PR01_HANDOFF.md, the approved plan, progress ledger and final review. Finish the remaining watchdog deadline correction, narrowly re-review it, and get all ten required engineering CI jobs green on the current head. Update the PR with the actual head, tested SHA, run URL and generated counts. Preserve scientific behavior and leave the PR unmerged for my review.

## Completed and verified locally

- Scientific/export fixtures, portable Windows startup checks, distinct socket-error diagnostics, scoped Ruff, Pillow >=10.1 metadata, offline watchdog reports, wheel/sdist verification, static Render and owned Docker checks, and the full CI workflow are implemented.
- All 35 original case IDs remain. The latest accepted pre-deadline-fix source and installed runs each passed 84 tests with zero failures/errors/skips. The installed worker recorded zero acquisition attempts. Actual Node argument captures confirmed all four ordinary exports used the installed wheel's JavaScript.
- The default build produced an sdist and a wheel from that sdist. Archive/resource/metadata, clean runtime installation, help/demo/server checks passed locally with documented retention adaptations.
- Ruff, adopted formatting, Node syntax, static Render and 39 documentation checks passed. Scientific modules, storage/schema, demo, frontend, Dockerfile, Render and run.sh bodies remain unchanged.
- Earlier installed-JavaScript masking and uncertain Docker-launch cleanup findings were fixed and re-reviewed. Historical validation notes remain explicitly separate from current evidence.

Read the [archived evidence](checkpoints/pr01/) for exact run circumstances. Local artifacts were retained under the user's deletion rule: ordinary physical cleanup and the unchanged full hosted watchdog path have not been established locally. Local Node was v24; CI requires Node 22. Docker was unavailable locally.

## Remaining work — do not mark ready yet

1. Resolve the final review's Important deadline finding. `verify_distribution.py` currently gives the installed watchdog an outer 200-second deadline, but its metadata, 180-second worker budget and cleanup can require 225 seconds. The outer layer can kill the watchdog before its owned worker is reaped. Prefer relying on the already bounded watchdog for that invocation, or use a coherent outer deadline with owned-tree fallback. Add a failing/passing virtual-clock regression; do not sleep for minutes. The unfinished regression is preserved in [this patch](checkpoints/pr01/unfinished-deadline-regression.patch), with its [red result](checkpoints/pr01/final-fix-red.json). On a clean clone, check it with `git apply --check --ignore-space-change docs/checkpoints/pr01/unfinished-deadline-regression.patch`, then apply it with `git apply --ignore-space-change docs/checkpoints/pr01/unfinished-deadline-regression.patch` and inspect it. The option accommodates Windows CRLF checkout lines. Finish the implementation and run it again. The patch is not an accepted final implementation; no unverified code from it was applied to the published runtime/test files.
2. Run affected tests and fresh source/installed verification for any changed test/runner code, then obtain a scoped review of the final fix. The existing wheel can be reused when runtime package files have not changed.
3. Get every current-head CI job green: Linux Python 3.10/3.11/3.12/3.13, Windows Python 3.12, Python 3.10 minimum NumPy/Pillow, quality, Linux/Windows distribution, and Docker. Inspect generated counts, errors/skips/acquisition attempts and cleanup evidence. A green run before the deadline correction does not close its review finding.
4. Record the reviewed base, implementation head, actual tested CI SHA (possibly a merge-test commit), exact accepted run URL and artifact evidence in the PR. Leave merge for the user; do not start PR02 before PR01 is green.

The [workflow runs](https://github.com/LincolnGothic/scientific-palette-lab/actions/workflows/ci.yml) and final PR description are the source of truth for later hosted outcomes. This checkpoint does not claim hosted CI, real Docker, ordinary cleanup or deployment success.

For local tests under the deletion restriction, the previous [retained audit helper](checkpoints/pr01/local-audit/run_retained_tests.py) is preserved. Copy it to an audit directory outside checkout, then invoke it with `--source` set to the repository root and `--report` set to an owned JSON path. It retains its test artifacts and does not establish physical cleanup. Use the appropriate installed Python environment and Node on PATH; use hosted CI for ordinary cleanup evidence. This helper is checkpoint material, not application runtime tooling.

## Scope and preferences

Keep unittest, the existing API/data model/framework, ΔE76, seed-2021 bootstrap, reference behavior and 55/30/15 recommendation baseline. No schema migrations, new corpus/history features, trained models, framework migration, licensing decision, live acquisition or cloud deployment belong in this PR. Future Core-500 eligibility means laboratory, animal or interventional research, excluding purely observational/computational papers; that future cohort work is not implemented here.

Do not delete local files or folders without listing exact targets and reasons and obtaining explicit yes/no approval. Do not bulk-delete artifacts. On Windows, keep newly installed Codex skills/plugins/runtime caches/downloaded repositories under the user's designated `D:\Codex_skill` locations; clarify an alternative if the new computer lacks that drive. Use PowerShell without profiles for routine checks. Keep changes minimal and verification evidence explicit.

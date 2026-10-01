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

> Continue from this PR01 branch and PR #2. Read docs/PR01_HANDOFF.md, the approved plan, the latest progress entries, final-fix review and parent verification. Check PR #2 for the exact current head, accepted tested SHA, CI run URL and generated counts. Resolve any remaining current-head CI failures or review feedback while preserving scientific behavior. The former unfinished deadline patch is already incorporated; do not apply it again. Leave the PR unmerged for my review and do not begin PR02.

## Completed and verified locally

- Scientific/export fixtures, portable Windows startup checks, distinct socket-error diagnostics, scoped Ruff, Pillow >=10.1 metadata, offline watchdog reports, wheel/sdist verification, static Render and owned Docker checks, and the full CI workflow are implemented.
- All 35 original case IDs remain. The latest accepted pre-deadline-fix source and installed runs each passed 84 tests with zero failures/errors/skips. The installed worker recorded zero acquisition attempts. Actual Node argument captures confirmed all four ordinary exports used the installed wheel's JavaScript.
- The default build produced an sdist and a wheel from that sdist. Archive/resource/metadata, clean runtime installation, help/demo/server checks passed locally with documented retention adaptations.
- Ruff, adopted formatting, Node syntax, static Render and 39 documentation checks passed. Scientific modules, storage/schema, demo, frontend, Dockerfile, Render and run.sh bodies remain unchanged.
- Earlier installed-JavaScript masking and uncertain Docker-launch cleanup findings were fixed and re-reviewed. Historical validation notes remain explicitly separate from current evidence.

The final watchdog deadline, older-Python discovery and Windows launcher-child log ownership findings are now fixed. The [scoped final-fix review](checkpoints/pr01/final-fix-review.md) passed spec and quality with no new defects. Fresh [source](checkpoints/pr01/final-source-suite.json) and [clean installed-wheel](checkpoints/pr01/final-clean-wheel-suite.json) retained runs each passed 88 tests with zero failures/errors/skips; the [parent verification](checkpoints/pr01/final-parent-verification.md) names the environments and limits. The former unfinished patch and its red result remain archived as history; do not apply that patch again.

Read the [archived evidence](checkpoints/pr01/) for exact run circumstances. Local artifacts were retained under the user's deletion rule: ordinary physical cleanup and the unchanged full hosted watchdog path have not been established locally. Local Node was v24; CI requires Node 22. Docker was unavailable locally.

## Hosted acceptance and next action

The corrected source has completed local covering/full verification and scoped review. The former checkpoint CI run had four source-suite failures; [its evidence](checkpoints/pr01/current-ci-findings.md) explains the discovery and Windows issues now addressed. That older run does not establish this corrected head.

Use [PR #2](https://github.com/LincolnGothic/scientific-palette-lab/pull/2) for the current implementation head, actual tested CI SHA (possibly a merge-test commit), accepted run URL, generated counts and any remaining failures. Require all ten jobs for the current head: Linux Python3.10/3.11/3.12/3.13, Windows Python3.12, Python3.10 minimum NumPy/Pillow, quality, Linux/Windows distribution and Docker. Inspect parent/worker counts, failures/errors/skips/acquisition attempts, installed origins/resources and cleanup evidence. The [workflow runs](https://github.com/LincolnGothic/scientific-palette-lab/actions/workflows/ci.yml) contain diagnostic artifacts; their presence alone is not a pass.

When every current-head gate is accepted, leave this PR and documentation PR #1 unmerged for the user's review. Do not start PR02 or deploy. Archived reports record their own historical heads and previous-computer paths; the latest PR metadata records hosted acceptance after this handoff was uploaded.

For local tests under the deletion restriction, the previous [retained audit helper](checkpoints/pr01/local-audit/run_retained_tests.py) is preserved. Copy it to an audit directory outside checkout, then invoke it with `--source` set to the repository root and `--report` set to an owned JSON path. It retains its test artifacts and does not establish physical cleanup. Use the appropriate installed Python environment and Node on PATH; use hosted CI for ordinary cleanup evidence. This helper is checkpoint material, not application runtime tooling.

## Scope and preferences

Keep unittest, the existing API/data model/framework, ΔE76, seed-2021 bootstrap, reference behavior and 55/30/15 recommendation baseline. No schema migrations, new corpus/history features, trained models, framework migration, licensing decision, live acquisition or cloud deployment belong in this PR. Future Core-500 eligibility means laboratory, animal or interventional research, excluding purely observational/computational papers; that future cohort work is not implemented here.

Do not delete local files or folders without listing exact targets and reasons and obtaining explicit yes/no approval. Do not bulk-delete artifacts. On Windows, keep newly installed Codex skills/plugins/runtime caches/downloaded repositories under the user's designated `D:\Codex_skill` locations; clarify an alternative if the new computer lacks that drive. Use PowerShell without profiles for routine checks. Keep changes minimal and verification evidence explicit.

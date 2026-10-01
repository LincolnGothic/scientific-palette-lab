# Task 5 documentation report

Status: DONE_WITH_CONCERNS — documentation and static checks complete. Hosted acceptance remains pending. This worker made no Git/D repository changes, deletions, installations, deployment or acquisition requests.

## Shipped staging changes

Only these three source files were edited:

- `docs/DEVELOPMENT.md` (new): clean base/developer environments and PowerShell interpreter alternatives; Python/NumPy/Pillow floors; Node 22 verification role; baseline/minimum constraints profiles; bounded offline runner and its limits; exact adopted Ruff lint/format scope; default wheel-from-sdist build and clean installed verifier; static Render/owned Docker contracts; actual JSON fields, phase status distinctions, report filenames and artifact names; workflow head/tested-SHA selection and scientific benchmark limits.
- `README.md`: narrow runtime/Windows/development-guide addition; replaced the unbounded example suite command with the production bounded offline runner; linked current workflow/evidence separation. Existing product, acquisition, scientific definitions, hosting and roadmap text remains.
- `VALIDATION.md`: added separate current engineering evidence without a fixed current test total; recorded the independent original Windows result (35 cases: 33 passed, one failure, one error), preservation of all original case IDs and the scope of subsequent fixes; relabeled historical release, browser and acquisition sections. The historical body remains verbatim, including its earlier release claims and pilot counts.

The documentation explicitly requires the final implementation PR description to identify reviewed base/head/tested SHA and exact accepted CI run URL after CI. It links the stable Engineering CI workflow page rather than inventing run IDs or embedding a stale manual current count. Each future run's source/installed counts are derived from its own reports.

## Verification

Ran `python pr01-implementation/artifacts/task5-doc-check.py` from `F:/codex/Project Plan` using the existing Python 3.10 interpreter with PowerShell profile loading disabled. **31 static checks passed**; machine evidence is `reports/task-5-doc-checks.json`.

Checks cover all local Markdown links in the three documents; documented options against each script's actual argparse AST; exact scoped format/lint and build command agreement with the workflow; artifact families; implementation report-key/status terminology; stable CI evidence links; absence of a fixed new current suite total; and verbatim historical body preservation against the existing D worktree VALIDATION file (read-only). Manually read the CLI, pyproject, both constraints profiles, complete workflow and three scripts to verify global-option ordering, Windows command shapes and independent build/static/Docker status descriptions.

The audit script and JSON are external retained task artifacts, not shipped source changes. No already-green source/installed suite or build was rerun for these Markdown edits. Production scientific-diff and original-case-ID final audits remain the controller's separate Task 5 acceptance work.

## Limits

- Hosted Linux/Windows/minimum profiles, Node 22 execution, ordinary physical cleanup and real Docker have not been claimed as passed. Local retained evidence does not establish those outcomes.
- Render parsing asserts agreement with the current reviewed config, not provider deployability. Docker uses a floating base/dependency resolution and reports missing base digest as unknown.
- Offline protection covers application `Remote.get`; it is not a blanket network isolation claim. Installs and GitHub infrastructure are separate.
- Engineering fixtures protect existing behavior without establishing representative extraction accuracy, real-corpus scientific findings or benchmark validation. Historical acquisition and browser observations remain explicitly separate.

Ready for documentation review and controller publication/hosted gates.

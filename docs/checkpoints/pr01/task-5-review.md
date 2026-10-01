# Task 5 documentation review

Reviewed commit: `36cfe275c5781877fc57734b86407b40adc02ad8` (parent `e74f7f88ceeafcd4498b21eb2806194f744397a5`).

## Verdict

Spec: PASS for the documentation implementation. Quality: PASS WITH ONE MINOR FIX. This does not approve final acceptance or merge: hosted matrix/minimum profiles, real Docker and ordinary cleanup remain pending.

The three-file diff documents the authorized installation, Windows commands, runtime-only Node distinction, exact Ruff scope, offline guard limits, constrained profiles, default wheel-from-sdist verification and report/artifact contracts. Current counts come from generated reports; the stable workflow link and required final PR base/head/tested-SHA/run identification do not invent completed CI evidence. Historical release/acquisition/browser prose is preserved and explicitly relabeled. Scientific behavior and future work are not expanded. The controller's 31 passing static checks and Task 4 source/installed/Ruff results were accepted as supplied evidence, not rerun.

## Findings

**Minor — development environments escape the existing ignore boundaries.** `docs/DEVELOPMENT.md:10–24,32–42,52–59,73` creates and references repository-root `.venv-base` and `.venv-dev`. The actual `.gitignore` ignores only `.venv/`; `.dockerignore` likewise excludes only `.venv`. Following the new guide therefore leaves both dependency trees visible to Git and includes them in the later documented Docker build context. The explicit Dockerfile COPY statements prevent them being installed in the image, but they still enlarge the context and invite accidental source-control inclusion.

Narrow fix: replace every guide reference to `.venv-base` with `.venv/base` and `.venv-dev` with `.venv/dev`, using Windows paths such as `.\.venv\base\Scripts\python.exe`. Keep the environments separate and fresh. This stays within the authorized Markdown file and uses the existing Git/Docker ignore rules; no new ignore file or deletion is needed. Recheck only the affected document command/path checks and all consistent references.

No Important finding. No additional script-contract inspection was needed after the supplied static checks and workflow agreement. Read-only inspection was limited to the relevant ignore rules, Dockerfile/package scope and workflow. No suites, builds, Git mutations, deletions, installations or acquisition requests were performed.


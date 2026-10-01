# Final PR01 branch review

Reviewed base `192abce8f86777911df0e1b4d62340c2a19e92f5` through head `f8f433ede7d9f293255b16bdc34bb2bda3a7ea2d`: all 21 changed paths and seven focused commits. Read the full supplied branch diff, original requirements, applicable approved-plan sections, progress ledger and task review/evidence reports. Earlier planning-only language is superseded by implementation authorization. Documentation PR #1 remains separate and unmerged.

**Spec verdict: changes required for one timeout/ownership boundary.** The implementation otherwise satisfies the approved PR01 code and documentation scope. **Quality verdict: changes required for the Important finding below.** No Critical or Minor findings. Hosted execution remains an independent acceptance gate.

## Strengths

- Production changes stay limited to accurate CLI startup diagnostics, an unused import and the approved dependency/tool metadata. The complete diff contains no scientific algorithm, storage/schema, frontend, demo, Dockerfile, Render or launcher changes. Diagnostic classifications preserve access-denied/address-conflict/address-unavailable distinctions and propagate unknown errors.
- Compact fixtures protect authored raster inputs, ΔE76/matching, complete-link grouping, distinct-variant medoids, paper/panel denominators, bootstrap compatibility, reference palettes and 55/30/15 recommendation arithmetic. Existing case IDs and meaningful assertions remain. Export checks exercise actual JavaScript, Python AST structure and HTTP CSV/JSON contracts.
- Installed verification compares archive and resource bytes, uses an independent runtime environment and checks import origin. The previously reported import-bound JavaScript default is fixed at call time; explicit mutation paths remain supported. The Docker uncertain-launch correction records ownership before launch and uses only its UUID name for cleanup.
- Source/installed reports distinguish missing evidence, failures, timeouts and unexecuted phases. Offline acquisition attempts are tracked even when swallowed. Documentation separates historical assertions, retained local evidence, current hosted gates and scientific benchmark limitations. The ignored-venv documentation correction is present.
- CI defines all ten required cells with separate base/dev/runtime environments, pinned dependencies/actions, full Windows coverage, minimum runtime coverage, failure propagation and diagnostic uploads. Scope has not expanded into PR02 or deployment.

## Important — installed-suite outer deadline can terminate its cleanup owner

**Location:** `scripts/verify_distribution.py:299–309`, specifically `timeout=200`, in combination with `scripts/run_tests.py:187–217` and its metadata/termination budgets.

The installed suite is launched through `subprocess.run(..., timeout=200)`. That deadline includes the watchdog process's startup metadata collection, which permits three consecutive ten-second command waits (`run_tests.py:54–67`). The watchdog starts its separate 180-second worker timeout only after metadata collection (`:189–214`), and then permits up to 15 seconds for Windows taskkill/reaping. Thus the legitimate inner failure/cleanup envelope can reach 225 seconds before final report handling. At 200 seconds, `subprocess.run` kills its direct child—the watchdog—without invoking that watchdog's worker-tree cleanup. The worker and any server descendants can remain alive; on POSIX the worker also has its own session. This violates the explicit bounded, owned-process cleanup requirement during the very deadlock path the watchdog exists to handle.

**Evidence:** a focused mock/virtual-clock execution of the actual `watchdog` function allowed 30 seconds for metadata and the configured 180-second worker budget, then 15 seconds for cleanup. Metadata ended at t=30, worker expiry occurred at t=210 and cleanup completed at t=225. The installed verifier's outer t=200 deadline therefore falls while the worker is still running. See `final-deadline-probe/evidence.json` and `final-deadline-probe/watchdog.json`. No real child was launched or terminated; no suite or build was rerun.

**Narrow fix:** give this already bounded installed-suite invocation a coherent deadline and owner. Either rely on its existing watchdog for this call, or make the outer budget encompass metadata, the full worker deadline and termination/reporting margin, with owned-tree cleanup preserved if the outer fallback fires. Add a focused regression for slow pre-worker metadata plus worker timeout so the outer layer cannot interrupt cleanup. Do not alter application or scientific behavior.

## Accepted evidence and remaining execution gates

Accepted controller evidence: final retained Windows source **84/84** and installed **84/84**, zero failures/errors/skips, zero real `Remote.get` attempts; actual Node consumer captures for all four ordinary wheel-JavaScript calls and five explicit mutation fixtures; Ruff full lint/scoped format, Node syntax and static Render checks passed. The recorded default sdist-to-wheel build, archive checks and real isolated offline installation passed under documented external retention adaptations. Those passing checks were not rerun in this review.

Hosted Linux Python 3.10–3.13, hosted Windows 3.12, minimum dependencies, Node 22, native temporary-file cleanup, the unchanged full installed watchdog execution, Bash syntax and real Docker build/container smoke remain unrun. These are pending execution gates, not additional review defects. Static Render agreement does not establish deployment, and none is required.

**Merge assessment: not ready.** Fix and narrowly re-review the timeout boundary, then publish the separate implementation draft PR and wait for every required hosted cell for the actual tested SHA. Keep documentation PR #1 open/unmerged and retain the reviewed base/head/tested-SHA/run identity in the final implementation PR evidence. No source/Git mutations, deletions, installation, live acquisition, deployment or additional agents were used during this review; only the requested review artifact and mocked-probe evidence were written.

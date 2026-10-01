# Task 2 review

Verdict: **approved with one minor finding**. No Critical or Important findings. The six-file change satisfies the approved Task 2 scope and is suitable to proceed to Tasks 3/4. The minor finding affects failure diagnostics, not process ownership or application behavior.

Reviewed base: `ac34a01e2d20496f0f7384bd1bd05ca3e86b0f7b`.

Reviewed head: `b8b295c2456a428b23b12586c27756cc5967050c`.

Inputs: `task-2-brief.md`, `task-2-report.md`, `task-2-diff.txt`, `progress.md`, and the six corresponding staging files. Accepted existing `task-2-full-suite.json`: **65 tests, zero failures/errors/skips on the retained Windows run**. No known passing suite was rerun. Linux matrix, real directory/duplicate-upload deletion, suite watchdog, CI and lint adoption remain downstream verification, not newly established facts.

## Findings

### Minor — malformed HTTP protocol failures lose owned diagnostics

Location: `tests/support.py:81` and `tests/support.py:90` (the two readiness request exception handlers).

Both handlers catch `OSError` and `ValueError`, but HTTP client protocol errors such as `http.client.BadStatusLine` and `http.client.IncompleteRead` are `HTTPException` subclasses outside those catch families. If the owned child sends a malformed status line, or truncates a length-delimited response, startup exits with the bare protocol exception rather than the helper's directory, URL, process state and bounded log tails. The `finally` still reaps the child and closes the logs, so this is a diagnostic completeness issue and is nonblocking.

Evidence: a focused, entirely mocked invocation of `running_server` injected `BadStatusLine("invalid status line")` from the no-proxy opener. Its result was `BadStatusLine: invalid status line`, with `terminated=True, waited=True`; the injected owned diagnostic string was absent. This check launched no real process, wrote/deleted no files and did not rerun a suite.

Suggested narrow improvement: include `http.client.HTTPException` in the two existing catch tuples and preserve the current last-error/AssertionError formatting. A small mock case would verify the diagnostic path without adding a new live fixture. The current application emits a well-formed local HTTP response, which limits the immediate impact.

## Specification compliance

| File | Assessment |
| --- | --- |
| `palette_lab/__main__.py:14-33,64-68` | Adds only recognized socket diagnostic classification and formatting. Uses symbolic errno constants and Windows 10048/10013/10049, includes original OS text/codes, retains the existing conflict recovery, adds portable `python -m` recovery, distinguishes uncertain access denial, and propagates unknown errors. Store creation, defaults, demo initialization, ValueError handling and scientific command behavior are preserved. |
| `tests/support.py:14-114` | Uses regular file logs with independent bounded read handles, a complete newline-terminated validated loopback announcement, monotonic readiness budget, no-proxy health checks, minimal state validation, bounded terminate/wait then kill/wait, and explicit reap failure. Log handles close after process cleanup. In-process shutdown/serve joins are bounded and never-started threads avoid shutdown. The exception-family finding above is the only issue identified. |
| `tests/test_cli.py:21-190` | Provides all specified mocked POSIX/Windows cases and unknown-error identity checks. Real occupied-listener coverage uses Windows exclusivity where available, checks the appropriate diagnostic category, and independently reconnects to the still-owned listener. Subprocess settings are sanitized; commands force UTF-8/unbuffered output and explicit isolated data/loopback/port-zero startup. Real early exit, absent/incomplete announcement, silent timeout, health failure and state failure cases assert reaping and log closure; mocked forced kill and reap failure cover deterministic ownership branches. |
| `tests/test_hosting.py:40-149` | Registers directory cleanup before Store construction, server closure before thread construction/start, and captured per-server cleanup across restart. Setup and thread-start failures are exercised. Added HTTP gates cover CSS/CSV, malformed credentials, foreign-host health and exact public health content. Traversal tests preserve literal request paths with `http.client` and include the approved existing outside-root targets. |
| `tests/test_pipeline.py:129-132,213-217` | Moves test-owned directory cleanup registration ahead of Store setup and honors RUNNER_TEMP. Duplicate import assertions verify stable figure identity, a single panel and exactly one referenced PNG. These implement the brief's explicit duplicate-upload verification requirement without production cleanup changes. |
| `tests/test_exports.py:27-112` | The ledger explicitly assigns the deferred HTTP export assertions to Task 2. Uses small offline reviewed Store/PNG fixtures for categorical, sequential, diverging and role palettes, with demo/excluded controls. Exercises actual HTTP JSON/CSV metadata, exact CSV schema, expected scope/counts/provenance/roles/order, and owns server/directory cleanup. Existing Node/browser export tests are unchanged. |

The diff contains no scientific algorithm, schema/storage, frontend, demo or application-route/body changes; no dependency/framework additions; no normal test-time external acquisition; and no production socket-policy or shutdown changes.

## Quality and review limits

- The file-log approach removes the Windows pipe-select/readline failure and avoids a fixed-port bind race. Error cases retain useful process evidence for the explicitly tested failures.
- Cleanup registration is placed at acquisition boundaries, and restart callbacks capture each server/thread rather than reading later reassigned attributes. The directory callback runs after the server callbacks.
- The traversal ruling is meaningfully applied: the owned `private.png` exists outside `assets` with an allowed suffix, and `/../__main__.py` names an existing Python file outside WEB. A narrowly scoped read of unchanged `app.py:197-207` confirmed these cases exercise the respective containment guards rather than merely nonexistent paths or an asset suffix rejection. No broader unchanged-code review was performed.
- Export expectations are authored independently of generated CSV; only the opaque family ID is cross-compared with JSON. Shared categorical demo/excluded controls detect leakage through the asserted one-paper/one-panel scope.
- Retained Windows evidence deliberately archives the duplicate-upload unlink and retains temporary directories. It verifies assertions/ownership and cannot certify actual physical deletion. The report states this limitation accurately; ordinary CI must exercise the real cleanup paths.
- No source, branch, installed package, repository content or existing artifact was edited or deleted during this review. The only added artifact is this review report.

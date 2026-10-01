# Validation evidence

## Current engineering verification

The [development guide](docs/DEVELOPMENT.md) documents the current commands, adopted scope, report fields and artifact names. Use [Engineering CI workflow runs](https://github.com/LincolnGothic/scientific-palette-lab/actions/workflows/ci.yml) to select the run associated with the current implementation head and confirm its actual tested SHA, which may be a PR merge-test commit. The final implementation PR description will identify the reviewed base, implementation head, tested SHA and exact accepted run URL. Inspect every required job and its artifacts; older green runs or uploaded diagnostics alone do not prove current success.

Derive current source and installed counts from the generated JSON reports (`testsRun`, `discovered`, `failures`, `errors`, `skips`, `status` and `remote_attempts`), including `distribution.json`'s `checks.unit_suite.result`. Read log/phase evidence for builds, quality, Render configuration and Docker separately. No fixed current total is maintained here. Hosted matrix, minimum-runtime, actual Docker and ordinary physical cleanup gates remain pending until the corresponding published run succeeds.

An independent Windows review of the original base found **35 tests: 33 passed, one failure and one error**. The historical “35 tests passed” statement below is preserved as a release claim, not current verified evidence. All 35 original case IDs remain; portability fixes and additional deterministic fixtures have since passed local retained source/installed checks. Those runs retain test artifacts and do not establish ordinary cleanup or hosted execution. The production changes are limited to CLI startup diagnostics, one unused import and dependency floors; scientific module, frontend, storage, configuration, demo, Dockerfile, Render and run.sh bodies remain unchanged.

Engineering tests protect the existing scientific contracts; they do not measure extraction accuracy on a representative real-figure benchmark. Historical live acquisition and browser observations below remain separate evidence and are not prerequisites for the offline suite.

## Historical first-release record · 30 September 2026

The following release statements and pilot observations are retained verbatim. Their dated outcomes and totals are historical and do not establish the current implementation head's CI status.

### Historical implementation checks

- **Hosted-mode checks passed:** the automated total is now **35 tests**, including password gating for UI/API/assets/exports, malformed credentials, external host/origin checks, minimal health response, and corpus survival across a server restart. JavaScript syntax and Python wheel packaging checks pass. The Render Blueprint parses with one instance, a persistent disk, and a required secret input. Docker is unavailable on this machine, so a container build and live deployment remain unverified. No hosting service or charges were activated.

- **Startup regression checks passed:** bringing the automated total to **29 tests**. A real occupied localhost port produces an actionable message and exit status 1 without a traceback; the existing listener remains available. A separate temporary instance starts on an OS-assigned port and serves the application successfully. The earlier development preview occupying port 8765 was stopped.

- **27 automated unittest cases passed.** Covered CIELAB reference values, raster extraction, meaningful neutral colors, categorical/ordered/role-aware matching, one-to-one color matching, flagship ISSNs, main/extended/floated JATS figures, current S3 URI conversion, published/manuscript version selection, collector idempotency, eligibility gates, paper-versus-panel votes, color-count denominators, real/demo separation, complete-link grouping, stale review rejection, re-extraction approval reset, bounded/nonoverlapping panel splitting, recommendation origin labels, locked-color constraints, bootstrap reproducibility, local upload deduplication, DOI normalization, source snapshot changes, and manuscript opt-in.
- **JavaScript syntax check passed** using `node --check palette_lab/web/app.js`.
- **Local HTTP checks passed:** state, reviewed-publication gates, separate data/flowchart statistics, recommendations for every color count from 3 through 8 in both categories, source-backed CSV/JSON exports, and host/origin rejection.
- **Browser checks passed:** compact and desktop layouts; dataset labels; separate chart/flowchart previews; 8-color controls; Science accepted-manuscript warning; extraction from a real Cell figure; selecting a synthetic chart's data-mark region to exclude annotation colors; re-extraction followed by review saving. No real publication panel was approved as part of this smoke test.

### Historical live acquisition pilot

This is a retrieval smoke test, not a representative statistical sample. Eight recent Nature records and selected final-version/accepted-manuscript candidates from the other two journals were used. Default years refer to the first publication date, which can precede the issue year.

| Journal | Papers with downloaded figures | Main figures | Version type |
|---|---:|---:|---|
| Nature | 8 | 39 | Final published versions |
| Cell | 1 | 7 | Final published version |
| Science | 2 | 8 | Licensed accepted manuscripts; opt-in retrieval, excluded from standard rankings |
| Total | 11 | 54 | 46 published figures + 8 accepted-manuscript figures |

Example source records:

- Nature: [A chiral fermionic valve driven by quantum geometry](https://pmc.ncbi.nlm.nih.gov/articles/PMC12756060/)
- Cell: [Uncovering phenotypic inheritance from single cells with Microcolony-seq](https://pmc.ncbi.nlm.nih.gov/articles/PMC12456302/)
- Science, accepted manuscript: [Moisture-responsive root-branching pathways identified in diverse maize breeding germplasm](https://pmc.ncbi.nlm.nih.gov/articles/PMC11956805/)
- Science, accepted manuscript: [Mitochondria protect against an intracellular pathogen by restricting access to folate](https://pmc.ncbi.nlm.nih.gov/articles/PMC12483063/)

Collection queries, errors, license/version records, JATS, source URLs, and image checksums are preserved in `data/`. Earlier unsuccessful acquisition attempts remain visible in collection history; the subsequent corrected runs succeeded. The downloaded publication figures are all unreviewed. The application correctly reports no real-corpus palette findings before review.

### Scientific limits of the historical checks

Passing implementation tests does not establish extraction accuracy across real scientific figures. Composite figures can contain photographs, microscopy, gradients, text, and multiple unrelated palettes. The real Cell extraction correctly raised many-shade/composite warnings. Selecting a relevant region and confirming the result is essential.

The next research validation should use a stratified manually annotated dataset and measure panel detection, chart classification, palette-size accuracy, and perceptual color recovery on held-out papers. A complete five-year census and a trained vision/recommendation model have not been produced in this release.

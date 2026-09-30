# First-release validation · 30 September 2026

## Implementation checks

- **Startup regression checks passed:** bringing the automated total to **29 tests**. A real occupied localhost port produces an actionable message and exit status 1 without a traceback; the existing listener remains available. A separate temporary instance starts on an OS-assigned port and serves the application successfully. The earlier development preview occupying port 8765 was stopped.

- **27 automated unittest cases passed.** Covered CIELAB reference values, raster extraction, meaningful neutral colors, categorical/ordered/role-aware matching, one-to-one color matching, flagship ISSNs, main/extended/floated JATS figures, current S3 URI conversion, published/manuscript version selection, collector idempotency, eligibility gates, paper-versus-panel votes, color-count denominators, real/demo separation, complete-link grouping, stale review rejection, re-extraction approval reset, bounded/nonoverlapping panel splitting, recommendation origin labels, locked-color constraints, bootstrap reproducibility, local upload deduplication, DOI normalization, source snapshot changes, and manuscript opt-in.
- **JavaScript syntax check passed** using `node --check palette_lab/web/app.js`.
- **Local HTTP checks passed:** state, reviewed-publication gates, separate data/flowchart statistics, recommendations for every color count from 3 through 8 in both categories, source-backed CSV/JSON exports, and host/origin rejection.
- **Browser checks passed:** compact and desktop layouts; dataset labels; separate chart/flowchart previews; 8-color controls; Science accepted-manuscript warning; extraction from a real Cell figure; selecting a synthetic chart's data-mark region to exclude annotation colors; re-extraction followed by review saving. No real publication panel was approved as part of this smoke test.

## Live acquisition pilot

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

## Limits of these checks

Passing implementation tests does not establish extraction accuracy across real scientific figures. Composite figures can contain photographs, microscopy, gradients, text, and multiple unrelated palettes. The real Cell extraction correctly raised many-shade/composite warnings. Selecting a relevant region and confirming the result is essential.

The next research validation should use a stratified manually annotated dataset and measure panel detection, chart classification, palette-size accuracy, and perceptual color recovery on held-out papers. A complete five-year census and a trained vision/recommendation model have not been produced in this release.

# Scientific Palette Lab · Chromatic

A local Python application for collecting and reviewing figure palettes from the **flagship Nature, Science, and Cell journals**. Data charts and flowcharts have separate analysis pipelines, color semantics, rankings, and visual previews. The default study window is **2021–2025**.

## Run

```bash
cd scientific_palette_lab
python3 -m venv .venv
.venv/bin/pip install -e .
bash run.sh
```

Open **http://127.0.0.1:8765**. Only NumPy and Pillow are needed; no API key, external database, JavaScript build, or paid model is required. `run.sh` can also use an existing Codex bundled Python runtime containing these dependencies.

```bash
# Optional separately labeled synthetic illustrations
bash run.sh serve --demo

# Small real pilot: scan one publication record per flagship journal
bash run.sh collect --limit 1

# Larger collection; the limit counts scanned metadata records, not eligible papers
bash run.sh collect --start-year 2021 --end-year 2025 --limit 100

# Explicit article identifiers, still checked against study scope
bash run.sh collect --journals Cell --pmcids PMC12456302 --limit 1

# Optional licensed accepted manuscripts: clearly tagged, excluded from standard rankings
bash run.sh collect --journals Science --pmcids PMC12483063 --include-manuscripts --limit 1

# Another corpus snapshot or local port
bash run.sh --data-dir ./another-study serve --port 8766

# Automated checks, using the same Python environment
.venv/bin/python -m unittest discover -s tests -v
```

## Workflow

1. **Collect articles:** Select years, flagship journals, and a scan limit. Europe PMC discovers OA records using exact print/electronic ISSNs. The current official PMC S3 service supplies published-version metadata, JATS XML, and matched main-figure images. Retracted versions, nonresearch article types, and identified supplementary/extended-data figures are excluded. Published versions are preferred; accepted manuscripts are excluded unless explicitly enabled for retrieval. They remain tagged and excluded from standard rankings unless separately enabled in the analysis filters. Each article's experimental eligibility remains pending.
2. **Review queue:** Inspect the source and caption. Propose panel splits or enter nonoverlapping `[left, top, right, bottom]` pixel regions. Panel proposals are whitespace heuristics and must be inspected. They can miss boundaries or cut inside a chart.
3. **Extract colors:** Drag a rectangle over relevant data marks or legend swatches. The extraction region is recorded separately from the panel boundary. Extraction composites transparency on white, builds a weighted RGB histogram, and merges nearby colors in CIELAB. It estimates the observed number of colors without forcing a requested count. Neutral colors are omitted by default; enable them or manually add meaningful black/gray controls. Inspect shades created by transparency or anti-aliasing.
4. **Confirm:** Choose data chart versus flowchart, confirm encoding, correct colors and order, assign flowchart roles, and check original experimental eligibility. Reviewed panels from included papers enter the rankings. Re-extraction revokes approval. Splitting retires the parent to prevent double counting. Review snapshots and revision checks preserve corrections.
5. **Explore:** Filter by journal, year, figure kind, encoding, and color count. Set similarity to zero for exact palettes. Download source-backed CSV/JSON rankings.
6. **Recommend:** Choose 3–8 unique colors and optional exact required color, background, and simulated-separation filter. Preview chart encodings or flowchart roles. Copy HEX values or download Python plotting code / diagram role JSON.

## Nine functional modules

| Responsibility | Implementation |
|---|---|
| Study configuration | `palette_lab/config.py` |
| Corpus collection | `palette_lab/corpus.py` |
| Figure/panel handling | `palette_lab/figures.py` |
| Chart/diagram suggestions | `palette_lab/classify.py` |
| Color extraction and matching | `palette_lab/colors.py` |
| Storage, provenance, and review | `palette_lab/store.py` |
| Statistical analysis | `palette_lab/statistics.py` |
| Recommendations | `palette_lab/recommend.py` |
| Local interface and API | `palette_lab/app.py`, `palette_lab/web/` |

`palette_lab/demo.py` generates labeled synthetic examples outside the real dataset.

## Statistical definitions

- **Extraction unit:** An active panel, identified by its source figure and bounding box.
- **Eligibility:** Both panel review and paper-level experimental eligibility must be confirmed. Other/unknown panels do not count.
- **Palette size:** The number of unique HEX colors. A flowchart can use the same HEX in several roles; each unique HEX is counted once in its size, but role assignments are retained in matching.
- **Paper prevalence:** Papers using a palette family divided by included papers containing ≥1 reviewed panel of the **same figure kind, palette type, and color count**, within the selected filters. A paper receives at most one vote per family. Percentages across different sizes have different denominators. Multiple families per paper can make percentages sum above 100%.
- **Panel frequency:** Active eligible panels using the family. It is reported separately from paper prevalence.
- **Similarity:** Minimum bottleneck ΔE76 matching enforces one-to-one color matches. Categorical order is ignored; gradient order and flowchart roles are retained. Complete-link grouping requires all pairs within a family to meet the threshold, avoiding transitive similarity chains. Grouping is deterministic but depends on the threshold and corpus; family IDs are local snapshot identifiers, not permanent universal names.
- **Representative:** A real member palette selected as a medoid among distinct palette variants. No averaging generates a palette that was never observed.
- **Individual colors:** Exact HEX values counted once per paper/panel; these are a separate statistic from palette popularity.
- **Uncertainty:** `/api/statistics?kind=data&bootstrap=300` adds a deterministic exploratory paper bootstrap interval. It does not model extraction error, dependent laboratories, or access-selection bias. Counts within a reviewed finite corpus are descriptive. Sensitivity can be checked by repeating exports at several ΔE thresholds.

## Recommendations and visual styles

**Data charts** separate categorical, sequential, and diverging encodings. Ordered palettes display low-to-high ramps; categorical palettes display example data marks. Example preview values are synthetic. Python exports provide color cycles or colormap construction.

**Flowcharts** preserve fill, decision, border, text, connector, and group roles. Previews illustrate diagram nodes and arrows; label text is adapted for readability and is not claimed to reproduce every original diagram. Exports preserve the reviewed role assignments.

The initial recommender retrieves reviewed observed palettes and applies a transparent scoring baseline: 55% paper prevalence, 30% approximate simulated color separation (category/node-fill colors), 15% background contrast. Reference palettes are explicitly labeled, have no observed prevalence, and never enter frequency statistics. It does not train a neural network or claim that journal frequency proves visual quality. Sequential/diverging palettes need actual-value and midpoint inspection.

Color-vision previews use Machado et al. full-dichromacy linear-RGB matrices. ΔE76 separation and contrast heuristics are aids, not accessibility certification. Inspect thin lines, small markers, text on fills, and grayscale; use redundant shapes or line styles. The filter applies to categorical/node-fill separation, not continuous gradient neighbors.

## Data, limits, and reproducibility

- **Coverage:** Europe PMC/PMC is a repository-accessible OA subset, especially weighted toward biomedical/life-sciences coverage. It does not guarantee coverage of every OA paper in the three journals. Date-descending scan-limited pilots are not representative samples. Collection history reports query hits, scanned records, matched figures, skipped records, and errors. Figure failures are visible rather than silently filled with invented data.
- **Publication versions:** Many accessible Science/Cell records are accepted manuscripts. The collector offers explicit opt-in retrieval of licensed manuscripts, records their status, and keeps them out of standard final-version analysis. Their colors may differ from the published version. Local imports also have a distinct source label; users must verify their origin. Paper DOI normalization prevents local and repository imports from creating separate paper votes. Identical normalized figure images are deduplicated by SHA-256 within each paper.
- **Licenses:** Published-version license codes are recorded. The collector accepts licensed PMC OA material, including noncommercial/restricted license types; users must respect the specific license for their reuse or redistribution. Importing a local image does not prove its license. The app is local and does not publish or share source figures automatically.
- **Current retrieval service:** Uses the versioned PMC S3 structure documented in 2026, not the retired OA package lookup API. Version metadata distinguishes author manuscripts from final published articles; the largest version is not blindly assumed to be a published version. Download URLs are limited to the official services, bounded, retried, and verified against supplied MD5 checksums.
- **Storage:** `data/corpus.sqlite3`, `data/assets/`, downloaded JATS/metadata snapshots, image SHA-256, source URLs, extraction parameters, and review snapshots. The real and synthetic datasets remain separate. No real ranking is populated from demo data or built-in reference palettes.
- **Local server:** Binds to loopback only and checks request host/origin. It is a personal research tool, not an authenticated multiuser deployment. Uploaded images are size-limited. The browser uses local assets with no external JavaScript/font dependencies.
- **First-release boundaries:** No trained vision classifier, OCR legend segmentation, automatic semantic role recognition, vector/PDF color recovery, publisher-specific fallback, trained recommender, or comprehensive five-year statistical findings. Caption-based classification and whitespace splitting are review suggestions. Raster HEX values may be estimates. If assets are absent from the approved services, import an authorized figure image and record its source.

Recommended next development: build a stratified, manually annotated benchmark covering years, journals, chart types, diagrams, neutral controls, gradients, and transparency. Measure panel recall, classification error, palette-size accuracy, and color matching error; evaluate on held-out papers. Use those measured errors to decide whether to add a trained detector, vector parsing, or a learned ranking model.

## Primary documentation

- [Europe PMC API](https://europepmc.org/RestfulWebService)
- [PMC S3 service and version handling](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/)
- [PMC bucket structure](https://pmc-oa-opendata.s3.amazonaws.com/README.txt)
- [Machado et al. color-vision simulation](https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html)
- [Okabe–Ito reference](https://jfly.uni-koeln.de/color/)
- [Paul Tol reference palettes](https://sronpersonalpages.nl/~pault/)
- [The misuse of colour in science communication](https://www.nature.com/articles/s41467-020-19160-7)

NIH NLM NCBI PubMed Central Article Datasets provide source material through the [AWS open dataset](https://registry.opendata.aws/ncbi-pmc). This application is not endorsed by the journals, NLM, NIH, or HHS.

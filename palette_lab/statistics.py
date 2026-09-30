import hashlib
import json
from collections import Counter, defaultdict

import numpy as np

from .colors import palette_distance


def color_count(colors):
    return len({c["hex"] for c in colors})


def canonical(colors, ordered=False):
    values = [(c["hex"], c.get("role", "unassigned")) for c in colors]
    return json.dumps(values if ordered else sorted(values), separators=(",", ":"))


def eligible_panels(store, filters):
    dataset = filters.get("dataset", "real")
    rows = store.panels(dataset)
    output = []
    for p in rows:
        include_manuscripts = str(filters.get("include_manuscripts", False)).lower() in ("yes", "true", "1")
        if p["version_type"] == "accepted-manuscript" and not include_manuscripts:
            continue
        if not p["reviewed"] or p["eligibility"] != "included" or p["kind"] not in ("data", "flowchart") or not p["colors"]:
            continue
        if filters.get("kind", "data") != p["kind"]:
            continue
        if filters.get("journal") and filters["journal"] != p["journal"]:
            continue
        if filters.get("year") and int(filters["year"]) != p["year"]:
            continue
        if filters.get("palette_type") and filters["palette_type"] != p["palette_type"]:
            continue
        if filters.get("count") and int(filters["count"]) != color_count(p["colors"]):
            continue
        output.append(p)
    return output


def families(store, filters, threshold=8., bootstrap=0):
    threshold = float(threshold)
    if not 0 <= threshold <= 25:
        raise ValueError("Similarity threshold must be 0–25 ΔE76 (0 means exact colors).")
    panels = eligible_panels(store, filters)
    # Bucket by encoding and unique color count. Never merge charts with flowcharts.
    buckets = defaultdict(list)
    for p in panels:
        buckets[(p["kind"], p["palette_type"], color_count(p["colors"]))].append(p)
    results = []
    for key, records in sorted(buckets.items()):
        kind, ptype, n = key
        ordered = ptype in ("sequential", "diverging")
        records.sort(key=lambda p: (canonical(p["colors"], ordered), p["id"]))
        groups = []
        for p in records:
            # Complete-link criterion avoids merging a chain of dissimilar palettes.
            for group in groups:
                if all(palette_distance(p["colors"], other["colors"], ordered, kind == "flowchart") <= threshold for other in group):
                    group.append(p)
                    break
            else:
                groups.append([p])
        paper_ids = sorted({p["paper_id"] for p in records})
        draws = None
        if bootstrap:
            rng = np.random.default_rng(2021)
            draws = rng.integers(0, len(paper_ids), size=(min(int(bootstrap), 1000), len(paper_ids)))
        for group in groups:
            unique = {canonical(p["colors"], ordered): p for p in group}
            candidates = list(unique.values())
            representative = min(candidates, key=lambda p: (sum(palette_distance(p["colors"], q["colors"], ordered, kind == "flowchart") for q in candidates), canonical(p["colors"], ordered)))
            used_papers = {p["paper_id"] for p in group}
            per_journal = Counter(p["journal"] for p in group)
            per_year = Counter(str(p["year"]) for p in group)
            fid = hashlib.sha256((str(key) + canonical(representative["colors"], ordered)).encode()).hexdigest()[:12]
            row = {"id": fid, "kind": kind, "palette_type": ptype, "count": n, "colors": representative["colors"],
                   "paper_count": len(used_papers), "panel_count": len(group), "paper_denominator": len(paper_ids),
                   "panel_denominator": len(records), "prevalence": round(len(used_papers)/len(paper_ids), 6),
                   "exact_variants": len(unique), "by_journal": dict(per_journal), "by_year": dict(per_year),
                   "sources": [{"panel_id": p["id"], "paper_id": p["paper_id"], "label": p["label"], "journal": p["journal"], "year": p["year"], "title": p["title"], "url": p["source_url"], "license": p["license"], "version_type": p["version_type"]} for p in group]}
            if draws is not None:
                vector = np.array([pid in used_papers for pid in paper_ids])
                row["bootstrap_interval"] = np.quantile(vector[draws].mean(axis=1), [.025, .975]).round(6).tolist()
            results.append(row)
    results.sort(key=lambda r: (-r["prevalence"], -r["paper_count"], -r["panel_count"], r["id"]))
    for i, r in enumerate(results):
        r["rank"] = i+1
    color_panels, color_papers = defaultdict(set), defaultdict(set)
    for p in panels:
        for color in {c["hex"] for c in p["colors"]}:
            color_panels[color].add(p["id"])
            color_papers[color].add(p["paper_id"])
    individual = [{"hex": c, "panels": len(v), "papers": len(color_papers[c])} for c,v in color_panels.items()]
    individual.sort(key=lambda c: (-c["papers"], -c["panels"], c["hex"]))
    return {"families": results, "individual_colors": individual[:40], "analyzed_panels": len(panels),
            "analyzed_papers": len({p["paper_id"] for p in panels}), "filters": filters, "threshold": threshold,
            "method": "complete-link, minimum bottleneck ΔE76; ordered gradients; role-aware flowcharts",
            "denominator": "Included papers with ≥1 reviewed panel of the same kind, palette type, and color count, within the selected filters.",
            "uncertainty_note": "Optional paper bootstrap is exploratory within this accessible corpus; it does not measure extraction error or remove OA selection bias.",
            "warning": "Rankings describe reviewed repository-accessible OA panels, not all Nature, Science, or Cell articles. Multiple palettes per paper can make prevalence sum exceed 100%."}

from .colors import accessibility, contrast
from .statistics import families

OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]
TOL_BRIGHT = ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB"]


def references(kind, count, ptype="categorical"):
    if kind == "data" and ptype == "categorical":
        result = [{"name": "Okabe–Ito reference subset", "colors": [{"hex": c, "role": "unassigned"} for c in OKABE_ITO[:count]],
                   "reference_url": "https://jfly.uni-koeln.de/color/"}]
        if count <= len(TOL_BRIGHT):
            result.append({"name": "Paul Tol bright reference subset", "colors": [{"hex": c, "role": "unassigned"} for c in TOL_BRIGHT[:count]],
                           "reference_url": "https://sronpersonalpages.nl/~pault/"})
        return result
    if kind == "flowchart":
        fills = ["#D8E9F5", "#F8DDB0", "#D3EBDC", "#E5DDF3", "#F3D9E5", "#DFE8B8"]
        return [{"name": "Illustrative role-based reference", "colors": [{"hex": c, "role": "fill" if i else "decision"} for i,c in enumerate(fills[:count-2])] +
                 [{"hex": "#64748B", "role": "connector"}, {"hex": "#17243A", "role": "text"}], "reference_url": ""}]
    return []


def recommend(store, options):
    kind = options.get("kind", "data")
    if kind not in ("data", "flowchart"):
        raise ValueError("Recommendations are available for data charts and flowcharts.")
    n = int(options.get("count", 4))
    if not 3 <= n <= 8:
        raise ValueError("Select 3–8 unique colors.")
    ptype = "roles" if kind == "flowchart" else options.get("palette_type", "categorical")
    if ptype not in ("categorical", "sequential", "diverging", "roles") or (kind == "data" and ptype == "roles"):
        raise ValueError("Select a compatible palette type.")
    background = options.get("background", "#FFFFFF")
    locked = options.get("locked", "").strip().upper()
    from .colors import rgb
    rgb(background)
    if locked:
        rgb(locked)
    threshold = float(options.get("threshold", 8))
    data = families(store, {**options, "kind": kind, "count": n, "palette_type": ptype}, threshold)
    candidates = [{**f, "name": f"Observed family {f['id'][:6]}", "origin": "observed"} for f in data["families"]]
    if options.get("include_references", True):
        candidates.extend({**r, "origin": "reference", "paper_count": 0, "panel_count": 0, "prevalence": None, "sources": []} for r in references(kind, n, ptype))
    output = []
    for c in candidates:
        values = [v["hex"] for v in c["colors"]]
        if locked and locked not in values:
            continue
        # For diagrams assess separation of node fills, not text versus connectors.
        role_values = [v["hex"] for v in c["colors"] if v.get("role") in ("fill", "decision", "group")]
        metrics = accessibility(values, background)
        fill_metrics = accessibility(role_values, background) if role_values else metrics
        is_categorical = ptype == "categorical" or kind == "flowchart"
        if options.get("cvd_filter") and is_categorical and fill_metrics["min_simulated_delta_e"] < 10:
            continue
        warnings = []
        if is_categorical and fill_metrics["min_simulated_delta_e"] < 10:
            warnings.append("Some category/fill colors may be difficult to distinguish in simulated color vision.")
        if kind == "data" and min(metrics["background_contrast"]) < 3:
            warnings.append("Some colors have low background contrast for small marks or thin lines.")
        if ptype == "sequential":
            lum = metrics["luminance"]
            if not (all(a <= b for a,b in zip(lum, lum[1:])) or all(a >= b for a,b in zip(lum, lum[1:]))):
                warnings.append("Sequential luminance is not monotonic; inspect whether the ramp suits the data.")
        if ptype == "diverging":
            warnings.append("Check the midpoint, balance, and value mapping on your actual data.")
        text = [v["hex"] for v in c["colors"] if v.get("role") == "text"]
        if kind == "flowchart" and text and role_values and min(contrast(t,f) for t in text for f in role_values) < 4.5:
            warnings.append("The observed text/fill pairing may have insufficient text contrast; preview adapts label text.")
        quality = min(fill_metrics["min_simulated_delta_e"] / 30, 1.) if is_categorical else .5
        popularity = c["prevalence"] or 0
        # Fixed transparent baseline, no claim of a trained model.
        score = .55 * popularity + .30 * quality + .15 * min(min(metrics["background_contrast"]) / 4.5, 1.)
        if c["origin"] == "reference":
            score -= .05
        output.append({**c, "score": round(score, 4), "metrics": metrics, "warnings": warnings})
    output.sort(key=lambda c: (-c["score"], c["name"]))
    return {"recommendations": output[:12], "options": options,
            "method": "Corpus retrieval with an explicit scoring baseline; no generative model or trained neural network.",
            "note": "Observed palettes and reference palettes are labeled separately. Recommendations cannot imply journal endorsement."}

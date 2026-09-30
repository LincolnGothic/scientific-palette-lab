"""Deterministic raster color estimates. These are review suggestions, not ground truth."""
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def rgb(hex_color):
    if not isinstance(hex_color, str) or not HEX.fullmatch(hex_color):
        raise ValueError("Colors must use six-digit HEX, for example #0072B2.")
    return np.array([int(hex_color[i:i + 2], 16) for i in (1, 3, 5)], dtype=float)


def rgb_to_lab(values):
    x = np.asarray(values, dtype=float) / 255.0
    x = np.where(x <= .04045, x / 12.92, ((x + .055) / 1.055) ** 2.4)
    xyz = x @ np.array([[.4124564, .3575761, .1804375],
                        [.2126729, .7151522, .0721750],
                        [.0193339, .1191920, .9503041]]).T
    xyz /= np.array([.95047, 1., 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])], axis=-1)


def delta_e(a, b):
    return float(np.linalg.norm(rgb_to_lab(rgb(a)) - rgb_to_lab(rgb(b))))


def luminance(color):
    x = rgb(color) / 255
    x = np.where(x <= .04045, x / 12.92, ((x + .055) / 1.055) ** 2.4)
    return float(x @ [.2126, .7152, .0722])


def contrast(a, b):
    la, lb = sorted([luminance(a), luminance(b)])
    return (lb + .05) / (la + .05)


def best_text(background):
    return max(("#111827", "#FFFFFF"), key=lambda c: contrast(c, background))


def accessibility(colors, background="#FFFFFF"):
    """Approximate full-dichromacy simulations, no accessibility certification."""
    values = np.array([rgb(c) for c in colors]) / 255
    lin = np.where(values <= .04045, values / 12.92, ((values + .055) / 1.055) ** 2.4)
    matrices = {
        "protanopia": [[.152286, 1.052583, -.204868], [.114503, .786281, .099216], [-.003882, -.048116, 1.051998]],
        "deuteranopia": [[.367322, .860646, -.227968], [.280085, .672501, .047413], [-.011820, .042940, .968881]],
        "tritanopia": [[1.255528, -.076749, -.178779], [-.078411, .930809, .147602], [.004733, .691367, .303900]],
    }
    def separation(vals):
        lab = rgb_to_lab(vals)
        return min((float(np.linalg.norm(a-b)) for i, a in enumerate(lab) for b in lab[i+1:]), default=100.)
    simulations = {}
    for name, mat in matrices.items():
        sim = np.clip(lin @ np.array(mat).T, 0, 1)
        srgb = np.where(sim <= .0031308, sim * 12.92, 1.055 * np.power(sim, 1/2.4) - .055)
        simulations[name] = {"colors": ["#%02X%02X%02X" % tuple(c) for c in np.rint(srgb * 255).astype(int)],
                             "min_delta_e": round(separation(srgb * 255), 2)}
    gaps = [simulations[n]["min_delta_e"] for n in matrices]
    return {"min_delta_e": round(separation(values * 255), 2), "simulations": simulations,
            "min_simulated_delta_e": min(gaps),
            "background_contrast": [round(contrast(c, background), 2) for c in colors],
            "luminance": [round(luminance(c), 3) for c in colors],
            "note": "Approximate simulation and ΔE76 checks; inspect actual marks. This is not an accessibility certification."}


def extract_palette(path: Path, bbox=None, include_neutrals=False, threshold=8., max_colors=24):
    if not 1 <= float(threshold) <= 25:
        raise ValueError("Extraction threshold must be 1–25 ΔE76.")
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGBA")
        if bbox:
            image = image.crop(tuple(bbox))
        white = Image.new("RGBA", image.size, "white")
        image = Image.alpha_composite(white, image).convert("RGB")
        # No resampling: interpolation creates colors that were not in the input.
        pixels = np.asarray(image).reshape(-1, 3)
        if len(pixels) > 400_000:
            pixels = pixels[::int(np.ceil(len(pixels) / 400_000))]
        labs = rgb_to_lab(pixels)
        keep = ~((labs[:, 0] > 96) & (np.linalg.norm(labs[:, 1:], axis=1) < 5))
        if not include_neutrals:
            keep &= np.linalg.norm(labs[:, 1:], axis=1) >= 6
        pixels = pixels[keep]
        if len(pixels) == 0:
            return {"colors": [], "flags": ["No data colors detected; select another region or include neutrals."], "confidence": "low"}
        # Weighted quantized histogram, then greedy perceptual merging of common bins.
        bins, inverse, counts = np.unique(pixels // 4, axis=0, return_inverse=True, return_counts=True)
        means = np.column_stack([np.bincount(inverse, weights=pixels[:, i]) / counts for i in range(3)])
        order = np.argsort(-counts, kind="stable")[:2048]
        clusters = []
        for index in order:
            lab = rgb_to_lab(means[index])
            distances = [np.linalg.norm(lab - c["lab"]) for c in clusters]
            if distances and min(distances) <= threshold:
                c = clusters[int(np.argmin(distances))]
                c["count"] += int(counts[index])
            else:
                clusters.append({"lab": lab, "rgb": np.rint(means[index]).astype(int), "count": int(counts[index])})
        clusters.sort(key=lambda c: -c["count"])
        # Tiny colors remain inspectable but flagged. This is not fixed-k clustering.
        meaningful = [c for c in clusters if c["count"] >= max(4, len(pixels) * .001)]
        chosen = meaningful[:max_colors]
        flags = ["Raster estimates: confirm against data marks or legend swatches."]
        if not include_neutrals:
            flags.append("Neutral colors omitted; add black/gray when they encode data.")
        if len(meaningful) > 12:
            flags.append("Many shades detected: possible gradient, photograph, composite figure, or transparency.")
        if len(meaningful) > max_colors:
            flags.append(f"Preview limited to {max_colors} colors; narrow the extraction region.")
        return {"colors": [{"hex": "#%02X%02X%02X" % tuple(c["rgb"]), "weight": round(c["count"] / len(pixels), 6), "role": "unassigned"} for c in chosen],
                "detected_count": len(meaningful), "flags": flags, "confidence": "low", "method": "weighted-raster-lab-v1", "threshold": threshold}


def palette_distance(a, b, ordered=False, role_aware=False):
    """Minimum bottleneck matching (small palettes); prevents many-to-one color matches."""
    if len(a) != len(b) or not a:
        return float("inf")
    if ordered:
        return max(delta_e(x["hex"], y["hex"]) for x, y in zip(a, b))
    costs = [[delta_e(x["hex"], y["hex"]) if not role_aware or x.get("role") == y.get("role") else float("inf") for y in b] for x in a]
    # Polynomial bipartite matching rather than exponential assignment enumeration.
    def feasible(bound):
        assigned = {}
        def visit(i, seen):
            for j, cost in enumerate(costs[i]):
                if cost <= bound and j not in seen:
                    seen.add(j)
                    if j not in assigned or visit(assigned[j], seen):
                        assigned[j] = i
                        return True
            return False
        return all(visit(i, set()) for i in range(len(a)))
    bounds = sorted({c for row in costs for c in row if np.isfinite(c)})
    if not bounds or not feasible(bounds[-1]):
        return float("inf")
    left, right = 0, len(bounds)-1
    while left < right:
        mid = (left+right)//2
        if feasible(bounds[mid]):
            right = mid
        else:
            left = mid+1
    return bounds[left]

import re
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image


def main_figures(xml_bytes):
    """Main JATS figures only; excludes back matter, supplementary and extended data."""
    root = ET.fromstring(xml_bytes)
    parents = {child: parent for parent in root.iter() for child in parent}
    result = []
    # JATS can store main figures in a root-level floats-group (common in Science).
    for index, fig in enumerate(root.findall(".//fig")):
        label = " ".join(fig.findtext("label", "").split())
        caption = " ".join(" ".join(fig.find("caption").itertext()).split()) if fig.find("caption") is not None else ""
        ancestors = []
        node = fig
        while node in parents:
            node = parents[node]
            ancestors.append(node.tag)
        if any(t in ("supplementary-material", "app", "back") for t in ancestors) or re.search(r"extended data|supplementary|^fig(?:ure)?\.?\s*s\d", label, re.I):
            continue
        hrefs = []
        for graphic in fig.findall(".//graphic"):
            href = graphic.get("{http://www.w3.org/1999/xlink}href", "")
            if href:
                hrefs.append(href)
        if hrefs:
            result.append({"id": fig.get("id", f"fig{index+1}"), "label": label or f"Figure {index+1}", "caption": caption, "hrefs": hrefs})
    return result


def suggest_panels(path, bbox=None):
    """Whitespace gutters propose panels, never approve or split the corpus silently."""
    with Image.open(path) as im:
        im = im.convert("RGB")
        origin = (bbox[0], bbox[1]) if bbox else (0, 0)
        if bbox:
            im = im.crop(bbox)
        w, h = im.size
        thumb = im.copy()
        thumb.thumbnail((600, 600))
        ink = np.min(np.asarray(thumb), axis=2) < 238
        tw, th = thumb.size
    def cuts(profile, size):
        blank = profile < .008
        runs = []
        start = None
        for i, val in enumerate(list(blank) + [False]):
            if val and start is None:
                start = i
            if not val and start is not None:
                if i-start >= max(5, size * .025) and start > size*.12 and i < size*.88:
                    runs.append((start + i)//2)
                start = None
        return runs[:3]
    xs = [0] + [round(x*w/tw) for x in cuts(ink.mean(axis=0), tw)] + [w]
    ys = [0] + [round(y*h/th) for y in cuts(ink.mean(axis=1), th)] + [h]
    boxes = [[xs[x]+origin[0], ys[y]+origin[1], xs[x+1]+origin[0], ys[y+1]+origin[1]] for y in range(len(ys)-1) for x in range(len(xs)-1)]
    return {"boxes": boxes, "method": "whitespace-gutters-v1", "warning": "Suggestions can cut inside charts. Inspect and edit before accepting."}


def validate_bbox(box, width, height):
    if not isinstance(box, list) or len(box) != 4 or any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in box):
        raise ValueError("Region must be [left, top, right, bottom] pixel coordinates.")
    x0, y0, x1, y1 = map(int, box)
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise ValueError("Region must lie within the image and have a positive size.")
    return [x0, y0, x1, y1]

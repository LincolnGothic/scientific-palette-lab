"""Compact v0.1 contracts; expectation rationales live beside the JSON fixture."""

import json
import math
import tempfile
import unittest
from itertools import combinations
from pathlib import Path
from types import MappingProxyType

import numpy as np
from PIL import Image

from palette_lab.colors import accessibility, delta_e, extract_palette, palette_distance, rgb_to_lab
from palette_lab.recommend import OKABE_ITO, TOL_BRIGHT, recommend, references
from palette_lab.statistics import families


EXPECTED = json.loads(
    (Path(__file__).parent / "fixtures" / "v01-scientific.json").read_text(encoding="utf-8")
)


def palette(*values, role="unassigned"):
    return tuple(MappingProxyType({"hex": c, "role": role}) for c in values)


def panel(pid, paper, colors, journal="Nature", year=2024, ptype="categorical", kind="data"):
    return MappingProxyType(
        {
            "id": pid,
            "paper_id": paper,
            "colors": colors,
            "journal": journal,
            "year": year,
            "palette_type": ptype,
            "kind": kind,
            "reviewed": True,
            "eligibility": "included",
            "version_type": "published",
            "label": pid,
            "title": "Fixture paper",
            "source_url": "",
            "license": "Fixture",
        }
    )


class Rows:
    """Store-shaped read-only adapter containing explicit immutable panel dictionaries."""

    def __init__(self, *rows):
        self.rows = tuple(rows)

    def panels(self, dataset):
        if dataset != "real":
            raise AssertionError("The scientific fixture contains only real rows")
        return self.rows


class BaselineTests(unittest.TestCase):
    def raster(self, name, image, **options):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / name
        image.save(path)
        return extract_palette(path, **options)

    def test_d65_srgb_and_delta_e76(self):
        np.testing.assert_allclose(rgb_to_lab([255, 255, 255]), [100, 0, 0], atol=0.01)
        np.testing.assert_allclose(rgb_to_lab([255, 0, 0]), [53.24, 80.09, 67.2], atol=0.03)
        np.testing.assert_allclose(rgb_to_lab([0, 0, 0]), [0, 0, 0], atol=1e-12)
        self.assertEqual(delta_e("#FF0000", "#FF0000"), 0)
        self.assertAlmostEqual(
            delta_e("#FF0000", "#0000FF"), EXPECTED["red_blue_delta_e"], delta=1e-6
        )

    def test_authored_two_three_four_color_rasters(self):
        for count in (2, 3, 4):
            values = ["#0072B2", "#E69F00", "#009E73", "#CC79A7"][:count]
            image = Image.new("RGB", (count * 20, 30), "white")
            for i, value in enumerate(values):
                image.paste(value, (i * 20, 5, i * 20 + 15, 25))
            with self.subTest(count=count):
                result = self.raster(f"bands-{count}.png", image)
                self.assertEqual({c["hex"] for c in result["colors"]}, set(values))
                self.assertEqual(result["detected_count"], count)
                self.assertEqual(result["method"], "weighted-raster-lab-v1")
                self.assertIn(
                    "Neutral colors omitted; add black/gray when they encode data.", result["flags"]
                )

    def test_semantic_neutrals_and_white_background(self):
        image = Image.new("RGB", (60, 20), "white")
        image.paste("#000000", (0, 5, 20, 15))
        image.paste("#808080", (20, 5, 40, 15))
        self.assertEqual(self.raster("neutral-default.png", image)["colors"], [])
        included = self.raster("neutral-included.png", image, include_neutrals=True)
        self.assertEqual({c["hex"] for c in included["colors"]}, {"#000000", "#808080"})
        self.assertEqual(included["detected_count"], 2)

    def test_alpha_composites_observed_color_and_omits_transparency(self):
        image = Image.new("RGBA", (40, 20), (0, 0, 255, 0))
        image.paste((255, 0, 0, 128), (0, 0, 20, 20))
        image.paste((0, 0, 255, 255), (20, 0, 30, 20))
        result = self.raster("alpha.png", image)
        self.assertEqual([c["hex"] for c in result["colors"]], ["#FF7F7F", "#0000FF"])
        self.assertEqual([c["weight"] for c in result["colors"]], [0.666667, 0.333333])
        self.assertEqual(result["detected_count"], 2)
        self.assertEqual(result["method"], "weighted-raster-lab-v1")
        self.assertEqual(result["confidence"], "low")

    def test_detection_count_is_independent_of_preview_cap(self):
        values = EXPECTED["preview_bands"]
        self.assertTrue(all(delta_e(a, b) > 1 for a, b in combinations(values, 2)))
        image = Image.new("RGB", (20 * len(values), 20))
        for i, value in enumerate(values):
            image.paste(value, (i * 20, 0, (i + 1) * 20, 20))
        result = self.raster("preview-cap.png", image, threshold=1, max_colors=3)
        self.assertEqual(result["detected_count"], 13)
        self.assertEqual(len(result["colors"]), 3)
        self.assertTrue({c["hex"] for c in result["colors"]}.issubset(values))
        self.assertIn("Preview limited to 3 colors; narrow the extraction region.", result["flags"])

    def test_matching_order_roles_infinity_and_bottleneck(self):
        a = palette("#FF0000", "#0000FF", "#00FF00")
        b = tuple(reversed(a))
        self.assertEqual(palette_distance(a, b), 0)
        self.assertGreater(palette_distance(a, b, ordered=True), 100)
        for left, right in (((), ()), (a, ()), (a, a[:2])):
            self.assertTrue(math.isinf(palette_distance(left, right)))
        roles = (
            MappingProxyType({"hex": "#0072B2", "role": "fill"}),
            MappingProxyType({"hex": "#111111", "role": "text"}),
        )
        swapped = (
            MappingProxyType({"hex": "#0072B2", "role": "text"}),
            MappingProxyType({"hex": "#111111", "role": "fill"}),
        )
        self.assertEqual(palette_distance(roles, swapped), 0)
        self.assertGreater(palette_distance(roles, swapped, role_aware=True), 50)
        self.assertTrue(
            math.isinf(
                palette_distance(
                    palette("#0072B2", role="fill"),
                    palette("#0072B2", role="text"),
                    role_aware=True,
                )
            )
        )
        close_reds = palette("#FF0000", "#FF0101")
        red_blue = palette("#FF0000", "#0000FF")
        # Every bijection must send one red to blue; choose the smaller of those two bottlenecks.
        expected = min(delta_e("#FF0000", "#0000FF"), delta_e("#FF0101", "#0000FF"))
        self.assertAlmostEqual(palette_distance(close_reds, red_blue), expected, delta=1e-9)
        self.assertGreater(expected, 100)
        self.assertEqual(
            palette_distance(close_reds, red_blue), palette_distance(red_blue, close_reds)
        )

    def test_complete_link_rejects_transitive_blue_chain(self):
        values = ["#0000C0", "#0000D0", "#0000E0"]
        bound = max(delta_e(values[0], values[1]), delta_e(values[1], values[2])) + 0.001
        self.assertGreater(delta_e(values[0], values[2]), bound)
        rows = Rows(*(panel(f"chain-{i}", str(i), palette(c)) for i, c in enumerate(values)))
        result = families(rows, {"kind": "data"}, threshold=bound)
        self.assertEqual(len(result["families"]), 2)
        self.assertEqual(sorted(f["panel_count"] for f in result["families"]), [1, 2])

    def test_ordered_encodings_keep_reviewed_order_in_families(self):
        values = palette("#0000FF", "#FFFFFF", "#FF0000")
        for ptype in ("sequential", "diverging"):
            with self.subTest(ptype=ptype):
                rows = Rows(
                    panel("forward", "a", values, ptype=ptype),
                    panel("reverse", "b", tuple(reversed(values)), ptype=ptype),
                )
                result = families(rows, {"kind": "data", "palette_type": ptype}, threshold=0)
                self.assertEqual(len(result["families"]), 2)
                self.assertEqual(
                    {tuple(c["hex"] for c in f["colors"]) for f in result["families"]},
                    {tuple(c["hex"] for c in values), tuple(c["hex"] for c in reversed(values))},
                )

    def test_hand_counted_members_medoid_denominators_and_bootstrap(self):
        rows = Rows(
            panel("a-blue-1", "a", palette("#0000C0")),
            panel("a-blue-2", "a", palette("#0000C0")),
            panel("a-blue-3", "a", palette("#0000C0")),
            panel("a-red", "a", palette("#FF0000")),
            panel("b-blue", "b", palette("#0000D0"), "Cell", 2023),
            panel("c-blue", "c", palette("#0000E0"), "Science", 2025),
            panel("d-red", "d", palette("#FF0000"), "Science", 2025),
            panel("e-two", "e", palette("#0072B2", "#E69F00")),
        )
        result = families(rows, {"kind": "data"}, threshold=25, bootstrap=100)
        self.assertEqual(result, families(rows, {"kind": "data"}, threshold=25, bootstrap=100))
        self.assertEqual((result["analyzed_papers"], result["analyzed_panels"]), (5, 8))
        projected = []
        for row in result["families"]:
            expected_fields = EXPECTED["families"][len(projected)]
            item = {k: row[k] for k in expected_fields if k not in ("hex", "members")}
            item["hex"] = [c["hex"] for c in row["colors"]]
            item["members"] = sorted(s["panel_id"] for s in row["sources"])
            self.assertEqual([c["role"] for c in row["colors"]], ["unassigned"] * row["count"])
            projected.append(item)
        self.assertEqual(projected, EXPECTED["families"])
        self.assertEqual(sum(f["prevalence"] for f in result["families"] if f["count"] == 1), 1.25)

    def recommendation_rows(self):
        return Rows(
            panel("good", "one", palette("#0072B2", "#E69F00", "#009E73")),
            panel("collision", "two", palette("#FF0000", "#FF0101", "#0000FF")),
        )

    def test_approximate_simulation_compatibility_and_score_arithmetic(self):
        metrics = accessibility(EXPECTED["recommendation_hex"][0])
        self.assertEqual(metrics["simulations"], EXPECTED["simulations"])
        self.assertEqual(metrics["min_simulated_delta_e"], 16.97)
        self.assertEqual(metrics["background_contrast"], [5.19, 2.25, 3.42])
        self.assertIn("not an accessibility certification", metrics["note"])
        quality_and_contrast = 0.30 * (16.97 / 30) + 0.15 * (2.25 / 4.5)
        self.assertEqual(round(0.55 * 0.5 + quality_and_contrast, 4), EXPECTED["white_scores"][0])
        self.assertEqual(round(quality_and_contrast - 0.05, 4), EXPECTED["white_scores"][2])

    def test_recommendation_scores_origins_order_counts_and_background(self):
        for background, scores in (("#FFFFFF", "white_scores"), ("#000000", "black_scores")):
            with self.subTest(background=background):
                rows = recommend(
                    self.recommendation_rows(),
                    {"kind": "data", "count": 3, "background": background},
                )["recommendations"]
                self.assertEqual([r["score"] for r in rows], EXPECTED[scores])
                self.assertEqual([r["origin"] for r in rows], EXPECTED["origins"])
                self.assertEqual(
                    [[c["hex"] for c in r["colors"]] for r in rows], EXPECTED["recommendation_hex"]
                )
                self.assertEqual([r["prevalence"] for r in rows], [0.5, 0.5, None, None])
                self.assertEqual([r["paper_count"] for r in rows], [1, 1, 0, 0])
                self.assertEqual([r["panel_count"] for r in rows], [1, 1, 0, 0])
                self.assertEqual(
                    [[c["role"] for c in r["colors"]] for r in rows], [["unassigned"] * 3] * 4
                )
                if background == "#FFFFFF":
                    self.assertTrue(
                        any("low background contrast" in w for w in rows[0]["warnings"])
                    )
                    self.assertTrue(
                        any("difficult to distinguish" in w for w in rows[1]["warnings"])
                    )

    def test_recommendation_cvd_lock_and_reference_constraints(self):
        options = {"kind": "data", "count": 3}
        for changes, indices in (
            ({"cvd_filter": True}, [0, 2, 3]),
            ({"locked": "#0072B2"}, [0, 2]),
            ({"include_references": False}, [0, 1]),
        ):
            with self.subTest(changes=changes):
                result = recommend(self.recommendation_rows(), {**options, **changes})[
                    "recommendations"
                ]
                self.assertEqual(
                    [r["score"] for r in result], [EXPECTED["white_scores"][i] for i in indices]
                )
                self.assertEqual(
                    [[c["hex"] for c in r["colors"]] for r in result],
                    [EXPECTED["recommendation_hex"][i] for i in indices],
                )
                self.assertEqual(
                    [r["origin"] for r in result], [EXPECTED["origins"][i] for i in indices]
                )

    def test_sequential_neighbors_use_fixed_quality_without_collision_filter(self):
        rows = Rows(
            panel("ramp", "one", palette("#FF0000", "#FF0101", "#0000FF"), ptype="sequential")
        )
        result = recommend(
            rows, {"kind": "data", "count": 3, "palette_type": "sequential", "cvd_filter": True}
        )["recommendations"]
        self.assertEqual(len(result), 1)
        self.assertLess(result[0]["metrics"]["min_simulated_delta_e"], 10)
        self.assertEqual([c["hex"] for c in result[0]["colors"]], ["#FF0000", "#FF0101", "#0000FF"])
        # Near-red has the minimum white contrast (3.99); sequential quality stays 0.5.
        self.assertEqual(result[0]["metrics"]["background_contrast"], [4.0, 3.99, 8.59])
        self.assertEqual(result[0]["score"], round(0.55 + 0.30 * 0.5 + 0.15 * (3.99 / 4.5), 4))

    def test_flowchart_fill_separation_and_full_palette_contrast(self):
        colors = (
            MappingProxyType({"hex": "#0072B2", "role": "decision"}),
            MappingProxyType({"hex": "#E69F00", "role": "fill"}),
            MappingProxyType({"hex": "#009E73", "role": "group"}),
            MappingProxyType({"hex": "#FFFFFF", "role": "text"}),
        )
        result = recommend(
            Rows(panel("flow", "one", colors, ptype="roles", kind="flowchart")),
            {"kind": "flowchart", "count": 4, "cvd_filter": True, "include_references": False},
        )["recommendations"]
        self.assertEqual(len(result), 1)
        row = result[0]
        self.assertEqual([c["role"] for c in row["colors"]], ["decision", "fill", "group", "text"])
        self.assertEqual(row["metrics"]["background_contrast"], [5.19, 2.25, 3.42, 1.0])
        self.assertEqual(row["score"], round(0.55 + 0.30 * (16.97 / 30) + 0.15 * (1 / 4.5), 4))
        self.assertTrue(any("text contrast" in w for w in row["warnings"]))

    def test_current_reference_arrays_and_roles(self):
        self.assertEqual(OKABE_ITO, EXPECTED["reference_arrays"]["okabe_ito"])
        self.assertEqual(TOL_BRIGHT, EXPECTED["reference_arrays"]["tol_bright"])
        self.assertEqual(references("flowchart", 4)[0]["colors"], EXPECTED["role_reference"])
        self.assertEqual(references("data", 3, "sequential"), [])


if __name__ == "__main__":
    unittest.main()

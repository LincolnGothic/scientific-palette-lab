"""Exercise actual browser downloadCode with Node's built-in VM; Node is required."""
import ast
import csv
import http.client
import io
import json
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
import urllib.parse
from http.server import ThreadingHTTPServer
from pathlib import Path

from PIL import Image

from palette_lab.app import Application, handler_for
from palette_lab.store import Store
from support import stop_http_server

HERE = Path(__file__).resolve().parent
APP_JS = HERE.parent / "palette_lab" / "web" / "app.js"


class HTTPExportTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(dir=os.environ.get("RUNNER_TEMP"))
        self.addCleanup(directory.cleanup)
        self.store = Store(Path(directory.name))
        self.fixtures = {}
        for ptype in ("categorical", "sequential", "diverging", "roles"):
            self.fixtures[ptype] = self.add_reviewed(ptype)
        self.add_reviewed("categorical", dataset="demo")
        self.add_reviewed("categorical", eligibility="excluded")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(Application(self.store)))
        self.addCleanup(self.server.server_close)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.addCleanup(stop_http_server, self.server, thread)
        thread.start()

    def add_reviewed(self, ptype, dataset="real", eligibility="included"):
        paper_id = f"fixture-{ptype}-{dataset}-{eligibility}"
        url = f"https://example.test/papers/{paper_id}"
        self.store.put_paper({"id": paper_id, "journal": "Nature", "year": 2024,
                              "title": paper_id, "source_url": url, "license": "CC BY",
                              "pmcid": "PMC123", "is_demo": dataset == "demo",
                              "metadata": {"s3": {"is_manuscript": False}}})
        asset = self.store.root / "assets" / f"{paper_id}.png"
        with Image.new("RGB", (3, 1)) as image:
            image.putdata([(255, 0, 0), (255, 255, 255), (0, 0, 255)])
            image.save(asset)
        self.store.put_figure(paper_id, "figure-1", "Figure 1", "Offline export fixture", asset, "", 1, 1)
        panel = next(p for p in self.store.panels(dataset) if p["paper_id"] == paper_id)
        roles = ("fill", "text", "connector") if ptype == "roles" else ("unassigned",) * 3
        colors = [{"hex": color, "role": role, "weight": 0}
                  for color, role in zip(("#FF0000", "#FFFFFF", "#0000FF"), roles)]
        kind = "flowchart" if ptype == "roles" else "data"
        self.store.review(panel["id"], {"kind": kind, "palette_type": ptype, "colors": colors,
                                      "revision": 0, "eligibility": eligibility,
                                      "confirmed_experimental": eligibility == "included"})
        return {"paper_id": paper_id, "url": url, "panel_id": panel["id"], "colors": colors, "kind": kind}

    def request(self, extension, filters):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request("GET", f"/api/export.{extension}?" + urllib.parse.urlencode(filters))
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.getheader("Cache-Control"), "no-store")
            filename = "palette-analysis.json" if extension == "json" else "palette-rankings.csv"
            self.assertEqual(response.getheader("Content-Disposition"), f'attachment; filename="{filename}"')
            self.assertEqual(response.getheader("Content-Type"),
                             "application/json; charset=utf-8" if extension == "json" else "text/csv; charset=utf-8")
            return response.read().decode("utf-8")
        finally:
            connection.close()

    def test_http_json_and_csv_preserve_reviewed_scope_sources_roles_and_order(self):
        columns = ["family_id", "kind", "palette_type", "color_count", "colors", "roles", "papers", "panels",
                   "paper_denominator", "paper_prevalence", "dataset", "threshold_delta_e76",
                   "source_paper_ids", "source_urls", "source_versions", "scope_filters"]
        for ptype, fixture in self.fixtures.items():
            with self.subTest(palette_type=ptype):
                filters = {"dataset": "real", "kind": fixture["kind"], "palette_type": ptype,
                           "journal": "Nature", "year": "2024", "count": "3", "threshold": "0"}
                result = json.loads(self.request("json", filters))
                self.assertEqual(result["filters"], filters)
                self.assertEqual(result["threshold"], 0)
                self.assertEqual(result["analyzed_papers"], 1)
                self.assertEqual(result["analyzed_panels"], 1)
                self.assertEqual(len(result["families"]), 1)
                family = result["families"][0]
                self.assertEqual(family["colors"], fixture["colors"])
                self.assertEqual(family["kind"], fixture["kind"])
                self.assertEqual(family["palette_type"], ptype)
                self.assertEqual(family["count"], 3)
                self.assertEqual(family["sources"], [{"panel_id": fixture["panel_id"], "paper_id": fixture["paper_id"],
                    "label": "Figure 1", "journal": "Nature", "year": 2024, "title": fixture["paper_id"],
                    "url": fixture["url"], "license": "CC BY", "version_type": "published"}])
                reader = csv.DictReader(io.StringIO(self.request("csv", filters), newline=""))
                self.assertEqual(reader.fieldnames, columns)
                rows = list(reader)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0], {
                    "family_id": family["id"], "kind": fixture["kind"], "palette_type": ptype, "color_count": "3",
                    "colors": "#FF0000;#FFFFFF;#0000FF",
                    "roles": ";".join(c["role"] for c in fixture["colors"]), "papers": "1", "panels": "1",
                    "paper_denominator": "1", "paper_prevalence": "1.0", "dataset": "real", "threshold_delta_e76": "0.0",
                    "source_paper_ids": json.dumps([fixture["paper_id"]]), "source_urls": json.dumps([fixture["url"]]),
                    "source_versions": '["published"]', "scope_filters": json.dumps(filters, sort_keys=True)})


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which("node")
        if cls.node is None:
            raise RuntimeError("ExportTests require Node.js on PATH; install/use Node before running test_exports.py.")

    def run_harness(self, cases, source=APP_JS):
        return subprocess.run([self.node, str(HERE / "export_harness.cjs"), str(source)],
                              input=json.dumps({"cases": cases}), capture_output=True,
                              text=True, encoding="utf-8", timeout=10, check=False)

    def case(self, name, ptype="categorical", origin="observed", dataset="real", kind="data"):
        colors = [{"hex": "#0000FF", "role": "unassigned"},
                  {"hex": "#FFFFFF", "role": "unassigned"},
                  {"hex": "#FF0000", "role": "unassigned"}]
        return {"name": name, "kind": kind, "dataset": dataset,
                "recOptions": {"palette_type": ptype},
                "row": {"id": "reviewed-family", "colors": colors,
                        "palette_type": ptype, "origin": origin}}

    def exports(self, cases):
        result = self.run_harness(cases)
        self.assertEqual(result.returncode, 0, result.stderr)
        envelope = json.loads(result.stdout)
        self.assertEqual(set(envelope), {"exports"})
        self.assertEqual([item["case"] for item in envelope["exports"]], [case["name"] for case in cases])
        return envelope["exports"]

    def python_tree(self, output, expected_colors):
        self.assertEqual(output["filename"], "chart-palette.py")
        content = output["content"]
        self.assertIn("\n", content)
        self.assertNotIn("\\n", content)
        tree = ast.parse(content)
        compile(content, output["filename"], "exec")
        assignments = [node for node in tree.body if isinstance(node, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == "colors" for t in node.targets)]
        self.assertEqual(len(assignments), 1)
        self.assertEqual(ast.literal_eval(assignments[0].value), expected_colors)
        return tree

    def test_categorical_export_uses_actual_cycler_assignment(self):
        case = self.case("categorical")
        output = self.exports([case])[0]
        tree = self.python_tree(output, ["#0000FF", "#FFFFFF", "#FF0000"])
        expected = ast.parse('plt.rcParams["axes.prop_cycle"] = cycler(color=colors)').body[0]
        assignments = [node for node in tree.body if isinstance(node, ast.Assign) and node is not tree.body[0]]
        self.assertEqual([ast.dump(node) for node in assignments], [ast.dump(expected)])
        imports = [ast.dump(node) for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertEqual(imports, [ast.dump(node) for node in ast.parse("import matplotlib.pyplot as plt\nfrom cycler import cycler").body])
        self.assertIn("Source family: reviewed-family", output["content"])

    def test_ordered_exports_preserve_sequence_and_colormap_ast(self):
        cases = [self.case("sequential", "sequential"), self.case("diverging", "diverging")]
        fallback = self.case("recommendation-type-fallback", "sequential")
        del fallback["row"]["palette_type"]
        cases.append(fallback)
        for output in self.exports(cases):
            with self.subTest(case=output["case"]):
                tree = self.python_tree(output, ["#0000FF", "#FFFFFF", "#FF0000"])
                expected = ast.parse('cmap = LinearSegmentedColormap.from_list("reviewed_palette", colors)').body[0]
                cmap = [node for node in tree.body if isinstance(node, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "cmap" for t in node.targets)]
                self.assertEqual([ast.dump(node) for node in cmap], [ast.dump(expected)])
                imports = [ast.dump(node) for node in tree.body if isinstance(node, ast.ImportFrom)]
                self.assertEqual(imports, [ast.dump(ast.parse("from matplotlib.colors import LinearSegmentedColormap").body[0])])

    def test_demo_and_reference_provenance_remains_explicit(self):
        cases = [self.case("demo", dataset="demo"), self.case("reference", origin="reference")]
        outputs = self.exports(cases)
        self.assertIn("SYNTHETIC DEMO: not a journal finding", outputs[0]["content"])
        self.assertIn("Reference colors, not observed journal frequency", outputs[1]["content"])
        self.assertIn("reference palette", outputs[1]["content"])
        for output in outputs:
            self.python_tree(output, ["#0000FF", "#FFFFFF", "#FF0000"])

    def test_flowchart_json_preserves_colors_roles_and_origin(self):
        colors = [{"hex": "#D8E9F5", "role": "decision"},
                  {"hex": "#F8DDB0", "role": "fill"},
                  {"hex": "#64748B", "role": "connector"},
                  {"hex": "#17243A", "role": "text"}]
        cases = [self.case("flow-observed", kind="flowchart"),
                 self.case("flow-reference", origin="reference", kind="flowchart")]
        del cases[0]["row"]["origin"]
        for case in cases:
            case["row"]["colors"] = colors
        for output, origin in zip(self.exports(cases), ("observed", "reference")):
            with self.subTest(origin=origin):
                self.assertEqual(output["filename"], "flowchart-palette.json")
                decoded = json.loads(output["content"])
                self.assertEqual(set(decoded), {"kind", "origin", "colors", "notes"})
                self.assertEqual(decoded["kind"], "flowchart")
                self.assertEqual(decoded["origin"], origin)
                self.assertEqual(decoded["colors"], colors)
                self.assertEqual(decoded["notes"], "Colors map to diagram roles. Verify text/fill contrast in the final figure.")

    def test_harness_rejects_missing_ambiguous_or_reordered_markers(self):
        source = APP_JS.read_text(encoding="utf-8")
        start = "async function downloadCode(row)"
        end = "document.addEventListener('click'"
        mutations = (("missing-start", source.replace(start, "async function relocatedDownload(row)"), "exactly one"),
                     ("missing-end", source.replace(end, "document.addEventListener('pointerup'"), "exactly one"),
                     ("duplicate-start", source + "\n" + start, "exactly one"),
                     ("duplicate-end", source + "\n" + end, "exactly one"),
                     ("reordered", end + "\n" + start, "out of order"))
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        for name, content, error in mutations:
            with self.subTest(mutation=name):
                path = Path(directory.name) / f"{name}.js"
                path.write_text(content, encoding="utf-8")
                result = self.run_harness([self.case(name)], source=path)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(error, result.stderr)


if __name__ == "__main__":
    unittest.main()

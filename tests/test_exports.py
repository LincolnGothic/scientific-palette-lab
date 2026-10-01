"""Exercise actual browser downloadCode with Node's built-in VM; Node is required."""
import ast
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
APP_JS = HERE.parent / "palette_lab" / "web" / "app.js"


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

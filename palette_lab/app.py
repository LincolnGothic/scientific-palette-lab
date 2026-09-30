import base64
import csv
import io
import json
import mimetypes
import threading
import traceback
import urllib.parse
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image

from . import __version__
from .classify import suggest_kind
from .colors import extract_palette
from .config import JOURNALS, Study
from .corpus import collect, save_image
from .demo import seed_demo
from .figures import suggest_panels, validate_bbox
from .recommend import recommend
from .statistics import families, eligible_panels

WEB = Path(__file__).parent / "web"


class Application:
    def __init__(self, store):
        self.store = store
        self.jobs = {}
        self.lock = threading.Lock()

    def start_collection(self, payload):
        study = Study(start_year=int(payload.get("start_year", 2021)), end_year=int(payload.get("end_year", 2025)),
                      journals=tuple(payload.get("journals", JOURNALS))).validate()
        limit = int(payload.get("limit", 5))
        if not 1 <= limit <= 10000:
            raise ValueError("Collection limit must be 1–10000 records per journal.")
        import re
        pmcids = payload.get("pmcids", [])
        if not isinstance(pmcids, list) or len(pmcids)>100 or any(not isinstance(p,str) or not re.fullmatch(r"PMC\d+",p) for p in pmcids):
            raise ValueError("Enter valid PMC identifiers.")
        with self.lock:
            if any(j["status"] == "running" for j in self.jobs.values()):
                raise ValueError("A collection is already running. Wait for it to finish.")
            jid = uuid.uuid4().hex
            job = {"id": jid, "status": "running", "message": "Connecting to Europe PMC…", "report": None}
            self.jobs[jid] = job
        def run():
            try:
                def progress(message):
                    with self.lock:
                        job["message"] = message
                report = collect(self.store, study, limit, progress, pmcids=pmcids, include_manuscripts=payload.get("include_manuscripts") is True)
                new_figures = sum(j["new_figures"] for j in report["journals"].values())
                with self.lock:
                    job.update(status="completed_with_errors" if report["errors"] else "completed", report=report,
                               message=f"Collection finished · {new_figures} new figures · {len(report['errors'])} reported issues")
            except Exception as exc:
                with self.lock:
                    job.update(status="failed", message=str(exc))
        threading.Thread(target=run, daemon=True).start()
        return {"job_id": jid}

    def state(self, dataset):
        panels = self.store.panels(dataset)
        for p in panels:
            p["suggestion"] = suggest_kind(p["caption"])
        with self.lock:
            jobs = [dict(j) for j in self.jobs.values()]
        return {"version": __version__, "overview": self.store.overview(dataset), "panels": panels,
                "jobs": jobs, "journals": list(JOURNALS), "dataset": dataset}

    def post(self, route, body):
        if route == "/api/collect":
            return self.start_collection(body)
        if route == "/api/demo":
            seed_demo(self.store)
            return {"ok": True, "note": "Synthetic examples are stored separately from real publication data."}
        if route == "/api/import":
            try:
                blob = base64.b64decode(body["image"], validate=True)
            except (ValueError, KeyError) as exc:
                raise ValueError("Upload a valid encoded image.") from exc
            journal, year = body.get("journal"), int(body.get("year", 0))
            if journal not in JOURNALS or not 1900 <= year <= 2100 or not str(body.get("title", "")).strip():
                raise ValueError("Specify a flagship journal, publication year, and paper title.")
            doi = str(body.get("doi", "")).strip().lower().removeprefix("https://doi.org/")
            if doi and not doi.startswith("10."):
                raise ValueError("Enter a DOI beginning with 10., or leave it blank.")
            paper_id = "LOCAL-" + (uuid.uuid5(uuid.NAMESPACE_URL, doi).hex if doi else uuid.uuid4().hex)
            asset = self.store.root / "assets" / (uuid.uuid4().hex + ".png")
            try:
                width, height = save_image(blob, asset)
            except Exception:
                asset.unlink(missing_ok=True)
                raise ValueError("Cannot decode this image. Use PNG, JPEG, or TIFF under 25 megapixels.")
            paper_id = self.store.put_paper({"id": paper_id, "journal": journal, "year": year, "title": str(body["title"])[:2000],
                "doi": doi, "license": str(body.get("license", "User-supplied; verify reuse rights")),
                "source_url": f"https://doi.org/{doi}" if doi else "", "metadata": {"source": "local upload"}})
            import hashlib
            fid, new = self.store.put_figure(paper_id, hashlib.sha256(blob).hexdigest(), str(body.get("label", "Uploaded figure")), str(body.get("caption", "")), asset, "", width, height)
            if not new:
                asset.unlink(missing_ok=True)
            return {"figure_id": fid, "new": new}
        if route in ("/api/extract", "/api/suggest-panels", "/api/split", "/api/review"):
            pid = body.get("panel_id", "")
            p = self.store.panel(pid)
            if route == "/api/extract":
                bbox = validate_bbox(body.get("bbox", p["bbox"]), p["width"], p["height"])
                result = extract_palette(self.store.root / p["asset_path"], bbox, bool(body.get("include_neutrals", False)), float(body.get("threshold", 8)))
                self.store.set_extraction(pid, result, bbox)
                return result
            if route == "/api/suggest-panels":
                return suggest_panels(self.store.root / p["asset_path"], p["bbox"])
            if route == "/api/split":
                return {"panel_ids": self.store.split(pid, body.get("boxes", []))}
            if route == "/api/review":
                return self.store.review(pid, body)
        raise ValueError("Unknown API operation.")


def handler_for(app):
    class Handler(BaseHTTPRequestHandler):
        server_version = "PaletteLab/0.1"

        def send(self, status, body, content_type="application/json; charset=utf-8", filename=None):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
            if filename:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(body)

        def permitted(self):
            port = self.server.server_port
            host = self.headers.get("Host", "")
            allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
            if host not in allowed_hosts:
                return False
            origin = self.headers.get("Origin")
            return not origin or origin in {f"http://{h}" for h in allowed_hosts}

        def do_GET(self):
            if not self.permitted():
                return self.send(403, {"error": "Local requests only."})
            try:
                parsed = urllib.parse.urlparse(self.path)
                route = parsed.path
                query = {k: v[-1] for k,v in urllib.parse.parse_qs(parsed.query).items()}
                if route == "/api/state":
                    return self.send(200, app.state(query.get("dataset", "real")))
                if route == "/api/statistics":
                    return self.send(200, families(app.store, query, float(query.get("threshold", 8)), int(query.get("bootstrap", 0))))
                if route == "/api/recommend":
                    for k in ("include_references", "cvd_filter"):
                        if k in query:
                            query[k] = query[k].lower() == "true"
                    return self.send(200, recommend(app.store, query))
                if route.startswith("/api/preview/"):
                    p = app.store.panel(route.rsplit("/", 1)[-1])
                    with Image.open(app.store.root / p["asset_path"]) as im:
                        im = im.crop(p["bbox"])
                        im.thumbnail((1200, 1000))
                        output = io.BytesIO()
                        im.save(output, "PNG")
                    return self.send(200, output.getvalue(), "image/png")
                if route in ("/api/export.json", "/api/export.csv"):
                    result = families(app.store, query, float(query.get("threshold", 8)))
                    if route.endswith(".json"):
                        return self.send(200, result, filename="palette-analysis.json")
                    stream = io.StringIO()
                    writer = csv.writer(stream)
                    writer.writerow(["family_id", "kind", "palette_type", "color_count", "colors", "roles", "papers", "panels", "paper_denominator", "paper_prevalence", "dataset", "threshold_delta_e76", "source_paper_ids", "source_urls", "source_versions", "scope_filters"])
                    for f in result["families"]:
                        writer.writerow([f["id"],f["kind"],f["palette_type"],f["count"],";".join(c["hex"] for c in f["colors"]),";".join(c["role"] for c in f["colors"]),f["paper_count"],f["panel_count"],f["paper_denominator"],f["prevalence"],query.get("dataset", "real"),result["threshold"],
                                         json.dumps(sorted({s["paper_id"] for s in f["sources"]})), json.dumps(sorted({s["url"] for s in f["sources"] if s["url"]})),
                                         json.dumps(sorted({s["version_type"] for s in f["sources"]})), json.dumps(query, sort_keys=True)])
                    return self.send(200, stream.getvalue().encode(), "text/csv; charset=utf-8", "palette-rankings.csv")
                if route.startswith("/assets/"):
                    path = (app.store.root / urllib.parse.unquote(route.lstrip("/"))).resolve()
                    if not path.is_relative_to((app.store.root / "assets").resolve()) or path.suffix.lower() != ".png":
                        return self.send(404, {"error": "Asset not found."})
                else:
                    path = (WEB / ("index.html" if route == "/" else route.lstrip("/"))).resolve()
                    if not path.is_relative_to(WEB.resolve()):
                        return self.send(404, {"error": "Not found."})
                if not path.is_file():
                    return self.send(404, {"error": "Not found."})
                return self.send(200, path.read_bytes(), mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            except (ValueError, KeyError, TypeError) as exc:
                self.send(400, {"error": str(exc)})
            except Exception:
                traceback.print_exc()
                self.send(500, {"error": "Server error; see the terminal for details."})

        def do_POST(self):
            if not self.permitted() or not self.headers.get("Content-Type", "").startswith("application/json"):
                return self.send(403, {"error": "Same-origin JSON requests only."})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 24_000_000:
                    return self.send(413, {"error": "Request is too large or empty (24 MB limit)."})
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("Request must be a JSON object.")
                return self.send(200, app.post(urllib.parse.urlparse(self.path).path, body))
            except (ValueError, KeyError, TypeError) as exc:
                self.send(400, {"error": str(exc)})
            except Exception:
                traceback.print_exc()
                self.send(500, {"error": "Server error; see the terminal for details."})

        def log_message(self, format, *args):
            if args and str(args[1]) not in ("200", "304"):
                super().log_message(format, *args)
    return Handler


def serve(store, port=8765):
    server = ThreadingHTTPServer(("127.0.0.1", port), handler_for(Application(store)))
    print(f"Scientific Palette Lab → http://127.0.0.1:{server.server_port}", flush=True)
    print(f"Corpus: {store.path}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

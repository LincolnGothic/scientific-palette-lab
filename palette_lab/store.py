import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import JOURNALS, KINDS, PALETTE_TYPES, ROLES
from .colors import rgb
from .figures import validate_bbox


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, root):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        (root / "assets").mkdir(exist_ok=True)
        self.path = root / "corpus.sqlite3"
        with self.connect() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS papers(
              id TEXT PRIMARY KEY, journal TEXT NOT NULL, year INTEGER NOT NULL,
              title TEXT NOT NULL, doi TEXT, pmcid TEXT, source_url TEXT,
              license TEXT, version TEXT, eligibility TEXT DEFAULT 'pending',
              is_demo INTEGER DEFAULT 0, metadata TEXT DEFAULT '{}', created_at TEXT);
            CREATE TABLE IF NOT EXISTS figures(
              id TEXT PRIMARY KEY, paper_id TEXT REFERENCES papers(id), source_key TEXT,
              label TEXT, caption TEXT, asset_path TEXT, source_url TEXT, sha256 TEXT,
              width INTEGER, height INTEGER, UNIQUE(paper_id, source_key));
            CREATE TABLE IF NOT EXISTS panels(
              id TEXT PRIMARY KEY, figure_id TEXT REFERENCES figures(id), label TEXT,
              bbox TEXT, extraction_bbox TEXT, kind TEXT DEFAULT 'unknown',
              palette_type TEXT DEFAULT 'unknown', colors TEXT DEFAULT '[]',
              extraction TEXT DEFAULT '{}', reviewed INTEGER DEFAULT 0,
              active INTEGER DEFAULT 1, notes TEXT DEFAULT '', revision INTEGER DEFAULT 0,
              updated_at TEXT);
            CREATE TABLE IF NOT EXISTS reviews(
              id INTEGER PRIMARY KEY, panel_id TEXT, snapshot TEXT, created_at TEXT);
            CREATE TABLE IF NOT EXISTS runs(
              id TEXT PRIMARY KEY, config TEXT, report TEXT, created_at TEXT);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def put_paper(self, paper):
        if paper["journal"] not in JOURNALS or not 1900 <= int(paper["year"]) <= 2100:
            raise ValueError("A paper must belong to Nature, Science, or Cell and have a valid year.")
        with self.connect() as db:
            doi = str(paper.get("doi", "")).strip().lower().removeprefix("https://doi.org/")
            existing = db.execute("SELECT id,journal,year FROM papers WHERE lower(doi)=? AND is_demo=?", (doi, int(paper.get("is_demo", False)))).fetchone() if doi else None
            if existing and (existing["journal"] != paper["journal"] or existing["year"] != int(paper["year"])):
                raise ValueError("This DOI already has a different journal or publication year in the corpus. Check its source metadata.")
            paper_id = existing["id"] if existing else paper["id"]
            db.execute("""INSERT INTO papers(id,journal,year,title,doi,pmcid,source_url,license,version,is_demo,metadata,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                license=CASE WHEN excluded.pmcid!='' THEN excluded.license ELSE papers.license END,
                version=CASE WHEN excluded.pmcid!='' THEN excluded.version ELSE papers.version END,
                pmcid=CASE WHEN excluded.pmcid!='' THEN excluded.pmcid ELSE papers.pmcid END,
                source_url=CASE WHEN excluded.source_url!='' THEN excluded.source_url ELSE papers.source_url END,
                metadata=CASE WHEN excluded.pmcid!='' OR papers.pmcid='' THEN excluded.metadata ELSE papers.metadata END""",
                (paper_id, paper["journal"], int(paper["year"]), paper["title"], doi, paper.get("pmcid", ""),
                 paper.get("source_url", ""), paper.get("license", ""), paper.get("version", ""), int(paper.get("is_demo", False)),
                 json.dumps(paper.get("metadata", {})), now()))
        return paper_id

    def assert_source_snapshot(self, paper_id, metadata):
        with self.connect() as db:
            old = db.execute("SELECT metadata FROM papers WHERE id=? OR (doi!='' AND lower(doi)=?)", (paper_id, str(metadata.get("doi", "")).lower())).fetchone()
        previous = json.loads(old["metadata"]).get("s3", {}) if old else {}
        if previous and (previous.get("xml_url") != metadata.get("xml_url") or previous.get("license_code") != metadata.get("license_code")):
            raise ValueError("Published source changed since this corpus snapshot. Use a new data directory to preserve reviewed provenance.")

    def put_figure(self, paper_id, key, label, caption, asset, source_url, width, height):
        with self.connect() as db:
            digest = hashlib.sha256(asset.read_bytes()).hexdigest()
            old = db.execute("SELECT id,sha256 FROM figures WHERE paper_id=? AND (source_key=? OR sha256=?) ORDER BY CASE WHEN source_key=? THEN 0 ELSE 1 END LIMIT 1", (paper_id, key, digest, key)).fetchone()
            if old:
                if old["sha256"] != digest:
                    # Do not leave reviewed palettes pointing at a different image.
                    raise ValueError("Source image changed; import a new corpus snapshot to preserve reviewed provenance.")
                return old["id"], False
            fid = uuid.uuid4().hex
            db.execute("INSERT INTO figures VALUES(?,?,?,?,?,?,?,?,?,?)", (fid, paper_id, key, label, caption, str(asset.relative_to(self.root)), source_url, digest, width, height))
            self._insert_panel(db, fid, label, [0, 0, width, height])
            return fid, True

    def _insert_panel(self, db, fid, label, bbox):
        pid = uuid.uuid4().hex
        db.execute("INSERT INTO panels(id,figure_id,label,bbox,updated_at) VALUES(?,?,?,?,?)", (pid, fid, label, json.dumps(bbox), now()))
        return pid

    def panels(self, dataset="real"):
        with self.connect() as db:
            rows = db.execute("""SELECT p.*,f.paper_id,f.asset_path,f.caption,f.width,f.height,f.source_url AS asset_source,
                a.journal,a.year,a.title,a.doi,a.pmcid,a.license,a.eligibility,a.is_demo,a.source_url,a.metadata AS paper_metadata
                FROM panels p JOIN figures f ON p.figure_id=f.id JOIN papers a ON f.paper_id=a.id
                WHERE p.active=1 AND a.is_demo=? ORDER BY a.journal,a.year DESC,f.label,p.label,p.id""", (int(dataset == "demo"),)).fetchall()
        output = []
        for r in rows:
            p = self.decode(dict(r))
            meta = json.loads(p.pop("paper_metadata"))
            manuscript = str(meta.get("s3", {}).get("is_manuscript", False)).lower() in ("yes", "true", "1", "y")
            p["version_type"] = "synthetic" if p["is_demo"] else "accepted-manuscript" if manuscript else "published" if meta.get("s3") else "local-import"
            output.append(p)
        return output

    def decode(self, row):
        for key in ("bbox", "colors", "extraction", "extraction_bbox"):
            if key in row:
                row[key] = json.loads(row[key]) if row[key] else None
        return row

    def panel(self, pid):
        with self.connect() as db:
            r = db.execute("""SELECT p.*,f.asset_path,f.width,f.height,f.paper_id,a.is_demo
                FROM panels p JOIN figures f ON p.figure_id=f.id JOIN papers a ON f.paper_id=a.id WHERE p.id=? AND p.active=1""", (pid,)).fetchone()
        if r is None:
            raise ValueError("Panel not found.")
        return self.decode(dict(r))

    def set_extraction(self, pid, result, bbox):
        with self.connect() as db:
            db.execute("UPDATE panels SET colors=?,extraction=?,extraction_bbox=?,reviewed=0,revision=revision+1,updated_at=? WHERE id=? AND active=1",
                       (json.dumps(result["colors"]), json.dumps(result), json.dumps(bbox), now(), pid))

    def split(self, pid, boxes):
        p = self.panel(pid)
        boxes = [validate_bbox(b, p["width"], p["height"]) for b in boxes]
        if not 1 <= len(boxes) <= 32:
            raise ValueError("Provide 1–32 panel regions.")
        for b in boxes:
            if not (p["bbox"][0] <= b[0] < b[2] <= p["bbox"][2] and p["bbox"][1] <= b[1] < b[3] <= p["bbox"][3]):
                raise ValueError("New regions must stay inside the panel being replaced.")
        for i, a in enumerate(boxes):
            for b in boxes[i+1:]:
                if max(a[0],b[0]) < min(a[2],b[2]) and max(a[1],b[1]) < min(a[3],b[3]):
                    raise ValueError("Panel regions must not overlap; overlapping panels would inflate counts.")
        with self.connect() as db:
            if db.execute("UPDATE panels SET active=0 WHERE id=? AND active=1", (pid,)).rowcount != 1:
                raise ValueError("This panel has already been replaced.")
            ids = [self._insert_panel(db, p["figure_id"], f"{p['label']} · {i+1}", b) for i,b in enumerate(boxes)]
        return ids

    def review(self, pid, values):
        p = self.panel(pid)
        kind, ptype = values.get("kind"), values.get("palette_type")
        if kind not in KINDS or ptype not in PALETTE_TYPES:
            raise ValueError("Select a valid figure kind and palette type.")
        if kind == "unknown":
            raise ValueError("Classify the panel before approving it.")
        if kind == "data" and ptype not in ("categorical", "sequential", "diverging"):
            raise ValueError("Data charts require a categorical, sequential, or diverging palette.")
        if kind == "flowchart" and ptype != "roles":
            raise ValueError("Flowcharts require role-based palettes.")
        colors = values.get("colors", [])
        if not isinstance(colors, list) or len(colors) > 32:
            raise ValueError("Supply at most 32 color-role entries.")
        cleaned = []
        pairs = set()
        for c in colors:
            rgb(c.get("hex"))
            role = c.get("role", "unassigned")
            if role not in ROLES or (kind == "flowchart" and role == "unassigned"):
                raise ValueError("Assign a role to every flowchart color.")
            if kind == "data":
                role = "unassigned"
            pair = (c["hex"].upper(), role)
            if pair in pairs:
                continue
            pairs.add(pair)
            cleaned.append({"hex": pair[0], "role": role, "weight": c.get("weight", 0)})
        if kind in ("data", "flowchart") and not cleaned:
            raise ValueError("Add at least one meaningful color, or classify this panel as other.")
        # Experimental status cannot be established from article-type metadata alone.
        eligibility = values.get("eligibility", "pending")
        if eligibility not in ("pending", "included", "excluded"):
            raise ValueError("Invalid article eligibility.")
        if eligibility == "included" and values.get("confirmed_experimental") is not True:
            raise ValueError("Confirm that this is eligible original experimental research.")
        with self.connect() as db:
            n = db.execute("""UPDATE panels SET kind=?,palette_type=?,colors=?,reviewed=1,notes=?,
                revision=revision+1,updated_at=? WHERE id=? AND revision=? AND active=1""",
                (kind, ptype, json.dumps(cleaned), str(values.get("notes", ""))[:5000], now(), pid, int(values.get("revision", -1)))).rowcount
            if n != 1:
                raise ValueError("This panel changed. Reload it before saving your review.")
            db.execute("UPDATE papers SET eligibility=? WHERE id=?", (eligibility, p["paper_id"]))
            db.execute("INSERT INTO reviews(panel_id,snapshot,created_at) VALUES(?,?,?)", (pid, json.dumps({**values, "colors": cleaned}), now()))
        return self.panel(pid)

    def save_run(self, config, report):
        with self.connect() as db:
            db.execute("INSERT INTO runs VALUES(?,?,?,?)", (uuid.uuid4().hex, json.dumps(config), json.dumps(report), now()))

    def overview(self, dataset="real"):
        demo = int(dataset == "demo")
        with self.connect() as db:
            papers = [dict(r) for r in db.execute("SELECT id,journal,year,title,eligibility,license FROM papers WHERE is_demo=?", (demo,))]
            runs = [dict(r) for r in db.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT 20")]
        panels = self.panels(dataset)
        return {"papers": len(papers), "paper_records": papers, "panels": len(panels),
                "reviewed": sum(p["reviewed"] for p in panels), "pending": sum(not p["reviewed"] for p in panels),
                "included_papers": sum(p["eligibility"] == "included" for p in papers),
                "runs": [{**r, "config": json.loads(r["config"]), "report": json.loads(r["report"])} for r in runs]}

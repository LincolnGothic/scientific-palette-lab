"""Europe PMC discovery + current PMC S3 media service. No publisher-page scraping."""
import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageOps

from .config import JOURNALS, Study
from .figures import main_figures

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
S3 = "https://pmc-oa-opendata.s3.amazonaws.com"


def normalize_url(url):
    """The 2026 metadata contains s3:// object URIs; convert only the official bucket."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme == "s3" and parsed.netloc == "pmc-oa-opendata":
        return S3 + parsed.path + (("?" + parsed.query) if parsed.query else "")
    return url


class Remote:
    def __init__(self, timeout=35, attempts=3):
        self.timeout, self.attempts, self.last = timeout, attempts, 0.

    def get(self, url, max_bytes=30_000_000):
        url = normalize_url(url)
        u = urllib.parse.urlparse(url)
        if u.scheme != "https" or u.hostname not in ("www.ebi.ac.uk", "pmc-oa-opendata.s3.amazonaws.com"):
            raise ValueError("Remote retrieval is restricted to Europe PMC and the official PMC S3 bucket.")
        for attempt in range(self.attempts):
            time.sleep(max(0, .28 - (time.monotonic() - self.last)))
            self.last = time.monotonic()
            request = urllib.request.Request(url, headers={"User-Agent": "ScientificPaletteLab/0.1 (open research palette analysis)"})
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    final = urllib.parse.urlparse(response.url)
                    if final.hostname not in ("www.ebi.ac.uk", "pmc-oa-opendata.s3.amazonaws.com"):
                        raise ValueError("Unexpected remote redirect.")
                    body = response.read(max_bytes + 1)
                    if len(body) > max_bytes:
                        raise ValueError("Remote asset exceeds the configured size limit.")
                    expected = urllib.parse.parse_qs(u.query).get("md5", [None])[0]
                    if expected and re.fullmatch(r"[0-9a-fA-F]{32}", expected) and hashlib.md5(body).hexdigest().lower() != expected.lower():
                        raise ValueError("Remote asset checksum mismatch.")
                    return body
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt+1 == self.attempts:
                    raise
            except (urllib.error.URLError, TimeoutError):
                if attempt+1 == self.attempts:
                    raise
            time.sleep(min(2 ** attempt, 4))

    def json(self, url):
        return json.loads(self.get(url))


def search_query(journal, study):
    identifiers = " OR ".join(f"ISSN:{v}" for v in JOURNALS[journal])
    return f"({identifiers}) AND FIRST_PDATE:[{study.start_year}-01-01 TO {study.end_year}-12-31] AND OPEN_ACCESS:Y"


def matches_journal(record, journal):
    meta = record.get("journalInfo", {}).get("journal", {})
    return any(meta.get(k) in JOURNALS[journal] for k in ("issn", "essn"))


def excluded_record(record):
    terms = [str(v).lower() for v in record.get("pubTypeList", {}).get("pubType", [])]
    excluded = ("review", "editorial", "correction", "retraction", "comment", "news", "expression of concern")
    return any(any(word in value for word in excluded) for value in terms)


def select_version(metadata, include_manuscripts=False):
    def yes(v):
        return str(v).lower() in ("yes", "y", "true", "1")
    candidates = [m for m in metadata if yes(m.get("is_pmc_openaccess")) and not yes(m.get("is_retracted"))
                  and (include_manuscripts or not yes(m.get("is_manuscript"))) and m.get("license_code") not in (None, "", "TDM")]
    if not candidates:
        raise ValueError("No licensed, non-retracted final published version is available in PMC S3.")
    # A larger version does not automatically mean a final published version.
    return sorted(candidates, key=lambda m: (yes(m.get("is_manuscript")), -int(m.get("version", 1))))[0]


def article_metadata(remote, pmcid, include_manuscripts=False):
    if not re.fullmatch(r"PMC\d+", pmcid):
        raise ValueError("Invalid PMCID.")
    url = S3 + "/?" + urllib.parse.urlencode({"list-type": 2, "prefix": pmcid + ".", "delimiter": "/"})
    root = ET.fromstring(remote.get(url))
    prefixes = [n.text for n in root.findall("{*}CommonPrefixes/{*}Prefix")]
    docs = []
    for prefix in prefixes:
        if re.fullmatch(pmcid + r"\.\d+/", prefix or ""):
            docs.append(remote.json(f"{S3}/{prefix}{prefix.rstrip('/')}.json"))
    return select_version(docs, include_manuscripts)


def match_media(hrefs, urls):
    matches = []
    for href in hrefs:
        base = Path(urllib.parse.unquote(urllib.parse.urlparse(href).path)).name
        stem = Path(base).stem
        for value in urls:
            # Fail clearly on upstream schema drift rather than inventing a URL.
            url = value if isinstance(value, str) else value.get("url", "")
            filename = Path(urllib.parse.unquote(urllib.parse.urlparse(url).path)).name
            if Path(filename).suffix.lower() in (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif") and (filename == base or Path(filename).stem == stem or Path(filename).stem == base):
                matches.append(url)
    return sorted(set(matches), key=lambda s: (Path(urllib.parse.urlparse(s).path).suffix.lower() not in (".tif", ".tiff", ".png"), s))


def save_image(body, path):
    with Image.open(io.BytesIO(body)) as source:
        if source.width * source.height > 25_000_000:
            raise ValueError("Image is too large (25 megapixel limit).")
        image = ImageOps.exif_transpose(source).convert("RGBA")
        image.save(path, "PNG")
        return image.size


def collect(store, study: Study, limit=5, progress=lambda _: None, remote=None, pmcids=None, include_manuscripts=False):
    study.validate()
    if not 1 <= int(limit) <= 10000:
        raise ValueError("Article limit must be 1–10000 per journal.")
    remote = remote or Remote()
    pmcids = list(dict.fromkeys(pmcids or []))
    if len(pmcids) > 100 or any(not re.fullmatch(r"PMC\d+", p) for p in pmcids):
        raise ValueError("Provide up to 100 valid PMC identifiers, for example PMC12483063.")
    report = {"provider": "Europe PMC + PMC S3", "journals": {}, "errors": [],
              "coverage_note": "Repository-accessible OA subset; not all journal OA articles. Original experimental eligibility requires review.",
              "selection": "Explicit PMCID selection within the study scope." if pmcids else "Publication date descending, limited pilot unless limit covers all hits.",
              "requested_pmcids": pmcids, "include_manuscripts": include_manuscripts}
    for journal in study.journals:
        query, cursor, scanned = search_query(journal, study), "*", 0
        if pmcids:
            query += " AND (" + " OR ".join(f"PMCID:{p}" for p in pmcids) + ")"
        counters = {"query": query, "available_oa_records": None, "scanned": 0, "papers_with_figures": 0, "new_figures": 0, "skipped": 0}
        report["journals"][journal] = counters
        try:
            while scanned < limit:
                url = EPMC + "/search?" + urllib.parse.urlencode({"query": query + " sort_date:y", "format": "json", "resultType": "core", "pageSize": min(100, limit-scanned), "cursorMark": cursor})
                page = remote.json(url)
                counters["available_oa_records"] = page["hitCount"]
                records = page.get("resultList", {}).get("result", [])
                if not records:
                    break
                for record in records:
                    scanned += 1
                    counters["scanned"] = scanned
                    title = record.get("title", "Untitled")
                    progress(f"{journal}: {scanned}/{limit} · {title[:85]}")
                    if not matches_journal(record, journal) or excluded_record(record) or not record.get("pmcid"):
                        counters["skipped"] += 1
                        continue
                    try:
                        pmcid = record["pmcid"]
                        year = int(record["firstPublicationDate"][:4])
                        if not study.start_year <= year <= study.end_year:
                            raise ValueError("Record outside the selected publication window.")
                        meta = article_metadata(remote, pmcid, include_manuscripts)
                        xml = remote.get(meta["xml_url"])
                        root = ET.fromstring(xml)
                        if root.get("article-type") not in ("research-article", "brief-report", "rapid-communication"):
                            raise ValueError("Not an original research article according to JATS metadata.")
                        jats_issns = {n.text for n in root.findall(".//journal-meta/issn")}
                        if not jats_issns.intersection(JOURNALS[journal]):
                            raise ValueError("JATS journal identifiers do not match the selected flagship journal.")
                        paper_id = pmcid
                        store.assert_source_snapshot(paper_id, meta)
                        paper_id = store.put_paper({"id": paper_id, "journal": journal, "year": year, "title": title,
                            "doi": record.get("doi", ""), "pmcid": pmcid, "source_url": f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/",
                            "license": meta["license_code"], "version": str(meta.get("version", "")),
                            "metadata": {"record": record, "s3": meta, "query": query}})
                        assets = store.root / "assets" / pmcid
                        assets.mkdir(exist_ok=True)
                        (assets / "metadata.json").write_text(json.dumps(meta, indent=2))
                        (assets / "article.xml").write_bytes(xml)
                        found = 0
                        for fig in main_figures(xml):
                            candidates = match_media(fig["hrefs"], meta.get("media_urls", []))
                            if not candidates:
                                report["errors"].append({"journal": journal, "pmcid": pmcid, "figure": fig["id"], "error": "Main figure has no matching downloadable image."})
                                continue
                            source_url = normalize_url(candidates[0])
                            safe_id = hashlib.sha256(fig["id"].encode()).hexdigest()[:16]
                            asset = assets / (safe_id + ".png")
                            if not asset.exists():
                                width, height = save_image(remote.get(source_url), asset)
                            else:
                                with Image.open(asset) as im:
                                    width, height = im.size
                            _, new = store.put_figure(paper_id, fig["id"], fig["label"], fig["caption"], asset, source_url, width, height)
                            found += 1
                            counters["new_figures"] += int(new)
                        counters["papers_with_figures"] += int(found > 0)
                    except Exception as exc:
                        counters["skipped"] += 1
                        report["errors"].append({"journal": journal, "pmcid": record.get("pmcid"), "error": f"{type(exc).__name__}: {exc}"})
                next_cursor = page.get("nextCursorMark")
                if not next_cursor or next_cursor == cursor:
                    break
                cursor = next_cursor
        except Exception as exc:
            report["errors"].append({"journal": journal, "error": f"Discovery failed: {exc}"})
    store.save_run({**study.to_dict(), "limit_per_journal": limit, "include_manuscripts": include_manuscripts}, report)
    return report

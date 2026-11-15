"""Reproducible HTML extraction demo using only the Python standard library.

The scraper reads local HTML fixtures, follows rel="next" links, normalizes
fields, validates required values, removes duplicate IDs, and exports CSV,
JSON, SQLite, and optional XLSX files. It does not access third-party sites.
"""
from __future__ import annotations
import argparse, csv, json, logging, sqlite3
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
try:
    from .schemas import SCHEMAS
except ImportError:
    from schemas import SCHEMAS

LOG = logging.getLogger("portfolio_scraper")

class RecordParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.records: list[dict[str, str]] = []
        self.next_page: str | None = None
        self._record: dict[str, str] | None = None
        self._field: str | None = None
        self._buffer: list[str] = []
        self._link_href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "article" and a.get("data-record-id"):
            self._record = {"_record_id": a["data-record-id"] or ""}
        if tag == "a" and (a.get("rel") == "next" or "next" in (a.get("rel") or "").split()):
            self.next_page = a.get("href")
        if self._record is not None and a.get("data-field"):
            self._field = a["data-field"] or ""
            self._buffer = []
            if tag == "a" and a.get("href"):
                self._record[self._field] = a["href"] or ""

    def handle_data(self, data: str) -> None:
        if self._record is not None and self._field:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._record is not None and self._field and tag in {"span", "a"}:
            visible = " ".join("".join(self._buffer).split())
            self._record.setdefault(self._field, visible)
            self._field = None
            self._buffer = []
        if tag == "article" and self._record is not None:
            self.records.append(self._record)
            self._record = None
            self._field = None
            self._buffer = []

def parse_page(path: Path) -> tuple[list[dict[str, str]], str | None]:
    parser = RecordParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.records, parser.next_page

def scrape_dataset(dataset: str, fixture_root: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    if dataset not in SCHEMAS:
        raise ValueError(f"Unknown dataset: {dataset}")
    schema = SCHEMAS[dataset]
    first = fixture_root / dataset / "page-1.html"
    if not first.exists():
        raise FileNotFoundError(f"Missing fixture start page: {first}")
    queue = [first]
    visited: set[Path] = set()
    unique: dict[str, dict[str, str]] = {}
    pages = 0
    while queue:
        page = queue.pop(0).resolve()
        if page in visited:
            continue
        visited.add(page)
        if not page.is_file():
            LOG.warning("Skipping missing pagination target: %s", page)
            continue
        pages += 1
        records, next_page = parse_page(page)
        LOG.info("Read %d records from %s", len(records), page.name)
        for raw in records:
            row = {field: " ".join(str(raw.get(field, "")).split()) for field in schema["fields"]}
            key = row.get(schema["id_field"], "").strip() or raw.get("_record_id", "").strip()
            if not key:
                LOG.warning("Skipping record without a stable ID on %s", page.name)
                continue
            missing = [field for field in schema["required"] if not row.get(field, "").strip()]
            if missing:
                LOG.warning("Record %s has missing required fields: %s", key, ", ".join(missing))
                continue
            if key in unique:
                LOG.info("Duplicate ignored: %s", key)
                continue
            unique[key] = row
        if next_page:
            target = (page.parent / next_page).resolve()
            if target.parent == page.parent.resolve():
                queue.append(target)
            else:
                LOG.warning("Rejected pagination target outside fixture directory: %s", next_page)
    rows = list(unique.values())
    missing_optional = {field: sum(not r.get(field, "") for r in rows) for field in schema["fields"] if field not in schema["required"]}
    report = {"dataset": dataset, "pages_read": pages, "records_exported": len(rows), "required_fields": schema["required"], "optional_missing_values": missing_optional, "deduplication_key": schema["id_field"], "source_type": "local authored HTML test fixtures", "notice": "Synthetic demonstration records; not live third-party data."}
    return rows, report

def export_rows(dataset: str, rows: list[dict[str, str]], report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No valid records to export for {dataset}")
    fields = list(rows[0])
    with (output_dir / f"{dataset}.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    (output_dir / f"{dataset}.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / f"{dataset}-quality-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    db = output_dir / "portfolio_demo.sqlite"
    with sqlite3.connect(db) as conn:
        table = dataset
        columns = ", ".join(f'"{c}" TEXT' for c in fields)
        conn.execute(f'DROP TABLE IF EXISTS "{table}"')
        conn.execute(f'CREATE TABLE "{table}" ({columns})')
        placeholders = ",".join("?" for _ in fields)
        conn.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', [[r.get(c, "") for c in fields] for r in rows])
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        wb = Workbook(); ws = wb.active; ws.title = dataset[:31]
        ws.append(fields)
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="19334A")
            cell.alignment = Alignment(vertical="center")
        for row in rows: ws.append([row.get(c, "") for c in fields])
        ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
        for col in ws.columns:
            letter = col[0].column_letter
            ws.column_dimensions[letter].width = min(max(max(len(str(c.value or "")) for c in col)+2, 12), 42)
        wb.save(output_dir / f"{dataset}.xlsx")
    except ImportError:
        LOG.info("openpyxl not installed; skipping XLSX export")

def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local HTML-fixture scraping portfolio demo.")
    parser.add_argument("--dataset", choices=["all", *SCHEMAS], default="all")
    parser.add_argument("--fixture-root", type=Path, default=Path(__file__).parent / "fixtures")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "output")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s: %(message)s")
    targets = list(SCHEMAS) if args.dataset == "all" else [args.dataset]
    for dataset in targets:
        rows, report = scrape_dataset(dataset, args.fixture_root)
        export_rows(dataset, rows, report, args.output_dir)
        print(f"{dataset}: {len(rows)} records across {report['pages_read']} page(s) -> {args.output_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

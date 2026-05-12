from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from app.scripts.extract_kb_source_manifest import (
    extract_kb_document_id,
    infer_maintenance_pack,
    normalize_text,
    read_text_lossy,
    relpath,
    repo_root,
)

PORTFOLIO_FILENAME_RE = re.compile(
    r"[A-Za-z0-9_.-]+_PFDs_Portfolio\.pdf",
    re.IGNORECASE,
)
HOT_FIX_SECTION_RE = re.compile(
    r"Hot\s+Fix\s+Release\s+(.+?)\s+About\s+Window\s*:?\s*("
    r"[A-Za-z0-9_.-]+_PFDs_Portfolio\.pdf)",
    re.IGNORECASE | re.DOTALL,
)
BUG_OR_PATCH_NUMBER_RE = re.compile(r"\b\d{5,}\b")
WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class HtmlTable:
    rows: list[list[str]]


@dataclass(frozen=True)
class HotFixSection:
    hot_fix_release_label: str
    about_window_file: str


@dataclass(frozen=True)
class KbFixRow:
    kb_document_id: str | None
    source_html: str
    maintenance_pack: str | None
    hot_fix_release_label: str | None
    about_window_file: str | None
    table_index: int
    row_index: int
    bug_patch_number: str | None
    product: str | None
    category: str | None
    description: str | None
    extraction_status: str
    extraction_warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class KbFixDocument:
    kb_document_id: str | None
    source_html: str
    source_html_sha256: str
    source_html_size_bytes: int
    maintenance_pack: str | None
    hot_fix_section_count: int
    fix_table_count: int
    fix_row_count: int
    fix_rows: list[KbFixRow]
    extraction_warnings: list[str]


@dataclass(frozen=True)
class KbFixRowsManifest:
    manifest_type: str
    generated_utc: str
    source_root: str
    html_source_count: int
    document_count: int
    fix_row_count: int
    documents: list[KbFixDocument]
    warnings: list[str]


class TableExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[HtmlTable] = []
        self._table_depth = 0
        self._current_rows: list[list[str]] | None = None
        self._current_row: list[str] | None = None
        self._current_cell_parts: list[str] | None = None
        self._capture_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        if normalized == "table":
            self._table_depth += 1
            if self._table_depth == 1:
                self._current_rows = []
            return

        if self._table_depth < 1:
            return

        if normalized == "tr" and self._table_depth == 1:
            self._current_row = []
        elif normalized in {"td", "th"} and self._table_depth == 1:
            self._current_cell_parts = []
            self._capture_cell = True
        elif normalized == "br" and self._capture_cell and self._current_cell_parts is not None:
            self._current_cell_parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if self._table_depth < 1:
            return

        if normalized in {"td", "th"} and self._table_depth == 1:
            if self._current_row is not None and self._current_cell_parts is not None:
                self._current_row.append(clean_cell_text(" ".join(self._current_cell_parts)))
            self._current_cell_parts = None
            self._capture_cell = False
        elif normalized == "tr" and self._table_depth == 1:
            if self._current_rows is not None and self._current_row:
                self._current_rows.append(self._current_row)
            self._current_row = None
        elif normalized == "table":
            if self._table_depth == 1 and self._current_rows is not None:
                self.tables.append(HtmlTable(rows=self._current_rows))
                self._current_rows = None
            self._table_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._capture_cell and self._current_cell_parts is not None:
            self._current_cell_parts.append(data)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_cell_text(value: str) -> str:
    decoded = html.unescape(value)
    return WHITESPACE_RE.sub(" ", decoded).strip()


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def find_html_sources(source_root: Path) -> list[Path]:
    return sorted(
        path
        for path in source_root.rglob("*.html")
        if path.is_file() and not any(part.endswith("_files") for part in path.parts)
    )


def extract_tables(raw_html: str) -> list[HtmlTable]:
    parser = TableExtractor()
    parser.feed(raw_html)
    parser.close()
    return parser.tables


def extract_hot_fix_sections(page_text: str) -> list[HotFixSection]:
    sections: list[HotFixSection] = []
    for match in HOT_FIX_SECTION_RE.finditer(page_text):
        sections.append(
            HotFixSection(
                hot_fix_release_label=WHITESPACE_RE.sub(" ", match.group(1)).strip(" :-"),
                about_window_file=match.group(2),
            )
        )
    return sections


def header_index(headers: list[str]) -> dict[str, int]:
    normalized_headers = [normalize_header(header) for header in headers]
    indexes: dict[str, int] = {}

    for index, header in enumerate(normalized_headers):
        if "bug" in header and ("patch" in header or "number" in header):
            indexes["bug_patch_number"] = index
        elif header == "product" or header.endswith("_product"):
            indexes["product"] = index
        elif header == "category" or header.endswith("_category"):
            indexes["category"] = index
        elif "description" in header:
            indexes["description"] = index

    return indexes


def is_fix_table(table: HtmlTable) -> bool:
    if not table.rows:
        return False
    indexes = header_index(table.rows[0])
    return {"bug_patch_number", "product", "category", "description"}.issubset(indexes)


def get_cell(row: list[str], index: int | None) -> str | None:
    if index is None or index >= len(row):
        return None
    value = row[index].strip()
    return value or None


def extract_bug_patch_number(value: str | None) -> str | None:
    if not value:
        return None
    match = BUG_OR_PATCH_NUMBER_RE.search(value)
    return match.group(0) if match else None


def build_fix_row(
    *,
    kb_document_id: str | None,
    source_html: str,
    maintenance_pack: str | None,
    section: HotFixSection | None,
    table_index: int,
    row_index: int,
    indexes: dict[str, int],
    row: list[str],
) -> KbFixRow:
    raw_bug_patch = get_cell(row, indexes.get("bug_patch_number"))
    bug_patch_number = extract_bug_patch_number(raw_bug_patch)
    product = get_cell(row, indexes.get("product"))
    category = get_cell(row, indexes.get("category"))
    description = get_cell(row, indexes.get("description"))

    warnings: list[str] = []
    if raw_bug_patch and not bug_patch_number:
        warnings.append("Bug / patch cell did not contain a numeric identifier.")
    if not bug_patch_number:
        warnings.append("Missing bug / patch number.")
    if not product:
        warnings.append("Missing product.")
    if not category:
        warnings.append("Missing category.")
    if not description:
        warnings.append("Missing description.")

    return KbFixRow(
        kb_document_id=kb_document_id,
        source_html=source_html,
        maintenance_pack=maintenance_pack,
        hot_fix_release_label=section.hot_fix_release_label if section else None,
        about_window_file=section.about_window_file if section else None,
        table_index=table_index,
        row_index=row_index,
        bug_patch_number=bug_patch_number,
        product=product,
        category=category,
        description=description,
        extraction_status="EXTRACTED" if not warnings else "EXTRACTED_WITH_WARNINGS",
        extraction_warnings=warnings,
    )


def build_document(html_path: Path, repository_root: Path) -> KbFixDocument:
    raw_html = read_text_lossy(html_path)
    page_text = normalize_text(raw_html)
    source_html = relpath(html_path, repository_root)
    kb_document_id = extract_kb_document_id(raw_html, html_path)
    maintenance_pack = infer_maintenance_pack(html_path, page_text)
    sections = extract_hot_fix_sections(page_text)
    tables = [table for table in extract_tables(raw_html) if is_fix_table(table)]

    warnings: list[str] = []
    if not sections:
        warnings.append("No hot fix release sections detected.")
    if not tables:
        warnings.append("No fix tables detected.")
    if sections and tables and len(sections) != len(tables):
        warnings.append(
            f"Hot fix section count ({len(sections)}) does not match fix table count ({len(tables)}). "
            "Rows are associated by table order."
        )

    fix_rows: list[KbFixRow] = []
    for table_index, table in enumerate(tables):
        indexes = header_index(table.rows[0])
        section = sections[table_index] if table_index < len(sections) else None
        for row_index, row in enumerate(table.rows[1:], start=1):
            if not any(cell.strip() for cell in row):
                continue
            fix_rows.append(
                build_fix_row(
                    kb_document_id=kb_document_id,
                    source_html=source_html,
                    maintenance_pack=maintenance_pack,
                    section=section,
                    table_index=table_index,
                    row_index=row_index,
                    indexes=indexes,
                    row=row,
                )
            )

    return KbFixDocument(
        kb_document_id=kb_document_id,
        source_html=source_html,
        source_html_sha256=sha256_file(html_path),
        source_html_size_bytes=html_path.stat().st_size,
        maintenance_pack=maintenance_pack,
        hot_fix_section_count=len(sections),
        fix_table_count=len(tables),
        fix_row_count=len(fix_rows),
        fix_rows=fix_rows,
        extraction_warnings=warnings,
    )


def build_manifest(source_root: Path) -> KbFixRowsManifest:
    repository_root = repo_root()
    resolved_source_root = source_root.resolve()
    html_sources = find_html_sources(resolved_source_root)
    documents = [build_document(path, repository_root) for path in html_sources]

    warnings: list[str] = []
    if not html_sources:
        warnings.append(f"No KB HTML sources found under {source_root}.")

    return KbFixRowsManifest(
        manifest_type="kb_fix_rows.v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        source_root=relpath(resolved_source_root, repository_root),
        html_source_count=len(html_sources),
        document_count=len(documents),
        fix_row_count=sum(document.fix_row_count for document in documents),
        documents=documents,
        warnings=warnings,
    )


def write_manifest(manifest: KbFixRowsManifest, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Extract structured fix rows from downloaded KB HTML release tables."
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=root / "kbs",
        help="Directory containing downloaded KB HTML files. Defaults to <repo>/kbs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_fix_rows.json",
        help="Fix-row manifest output path. Defaults to <repo>/kbs/manifests/kb_fix_rows.json.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_manifest(args.source_root)
    write_manifest(manifest, args.output)

    warning_count = sum(len(document.extraction_warnings) for document in manifest.documents) + len(manifest.warnings)
    row_warning_count = sum(
        len(row.extraction_warnings)
        for document in manifest.documents
        for row in document.fix_rows
    )

    print(f"Wrote KB fix-row manifest: {args.output}")
    print(f"KB HTML sources: {manifest.html_source_count}")
    print(f"Fix rows extracted: {manifest.fix_row_count}")
    print(f"Document warnings: {warning_count}")
    print(f"Row warnings: {row_warning_count}")


if __name__ == "__main__":
    main()

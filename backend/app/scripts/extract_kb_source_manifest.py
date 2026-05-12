from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

PORTFOLIO_FILENAME_RE = re.compile(
    r"[A-Za-z0-9_.-]+_PFDs_Portfolio\.pdf",
    re.IGNORECASE,
)
KB_DOCUMENT_ID_RE = re.compile(r"documentId=(KB\d+)", re.IGNORECASE)
KB_ID_FALLBACK_RE = re.compile(r"\bKB\d+\b", re.IGNORECASE)
RELEASE_VERSION_RE = re.compile(r"CCS_(\d+(?:\.\d+)*)_MP", re.IGNORECASE)
MAINTENANCE_PACK_RE = re.compile(r"MP\s*(\d+)", re.IGNORECASE)
HOT_FIX_SECTION_RE = re.compile(
    r"Hot\s+Fix\s+Release\s+(.+?)\s+About\s+Window\s*:?\s*("
    r"[A-Za-z0-9_.-]+_PFDs_Portfolio\.pdf)",
    re.IGNORECASE | re.DOTALL,
)
SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b.*?</\1>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class PortfolioRecord:
    filename: str
    path: str
    sha256: str
    size_bytes: int
    release_version: str | None


@dataclass(frozen=True)
class ReferencedPortfolioRecord:
    filename: str
    found: bool
    path: str | None
    sha256: str | None
    size_bytes: int | None
    release_version: str | None


@dataclass(frozen=True)
class HotFixSectionRecord:
    hot_fix_release_label: str
    about_window_file: str
    portfolio_found: bool
    portfolio_path: str | None


@dataclass(frozen=True)
class KbDocumentRecord:
    kb_document_id: str | None
    source_html: str
    source_html_sha256: str
    source_html_size_bytes: int
    maintenance_pack: str | None
    referenced_portfolios: list[ReferencedPortfolioRecord]
    hot_fix_sections: list[HotFixSectionRecord]
    extraction_warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourceInventoryManifest:
    manifest_type: str
    generated_utc: str
    source_root: str
    html_source_count: int
    portfolio_file_count: int
    kb_documents: list[KbDocumentRecord]
    unreferenced_portfolios: list[PortfolioRecord]
    missing_portfolios: list[str]
    warnings: list[str]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def read_text_lossy(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def normalize_text(raw_html: str) -> str:
    without_scripts = SCRIPT_STYLE_RE.sub(" ", raw_html)
    without_tags = TAG_RE.sub(" ", without_scripts)
    decoded = html.unescape(without_tags)
    return WHITESPACE_RE.sub(" ", decoded).strip()


def find_html_sources(source_root: Path) -> list[Path]:
    return sorted(
        path
        for path in source_root.rglob("*.html")
        if path.is_file() and not any(part.endswith("_files") for part in path.parts)
    )


def find_portfolios(source_root: Path) -> list[Path]:
    return sorted(
        path
        for path in source_root.rglob("*_PFDs_Portfolio.pdf")
        if path.is_file()
    )


def extract_kb_document_id(raw_html: str, html_path: Path) -> str | None:
    match = KB_DOCUMENT_ID_RE.search(raw_html)
    if match:
        return match.group(1).upper()

    fallback = KB_ID_FALLBACK_RE.search(raw_html)
    if fallback:
        return fallback.group(0).upper()

    filename_fallback = KB_ID_FALLBACK_RE.search(html_path.name)
    if filename_fallback:
        return filename_fallback.group(0).upper()

    return None


def infer_maintenance_pack(html_path: Path, page_text: str) -> str | None:
    for value in (html_path.name, page_text[:5000]):
        match = MAINTENANCE_PACK_RE.search(value)
        if match:
            return f"MP {match.group(1)}"
    return None


def infer_release_version(filename: str) -> str | None:
    match = RELEASE_VERSION_RE.search(filename)
    if match:
        return match.group(1)
    return None


def extract_referenced_portfolio_filenames(raw_html: str, page_text: str) -> list[str]:
    found = set(PORTFOLIO_FILENAME_RE.findall(raw_html))
    found.update(PORTFOLIO_FILENAME_RE.findall(page_text))
    return sorted(found, key=str.lower)


def extract_hot_fix_sections(page_text: str, portfolio_by_name: dict[str, PortfolioRecord]) -> list[HotFixSectionRecord]:
    sections: list[HotFixSectionRecord] = []
    for match in HOT_FIX_SECTION_RE.finditer(page_text):
        release_label = WHITESPACE_RE.sub(" ", match.group(1)).strip(" :-")
        portfolio_name = match.group(2)
        portfolio = portfolio_by_name.get(portfolio_name.lower())
        sections.append(
            HotFixSectionRecord(
                hot_fix_release_label=release_label,
                about_window_file=portfolio_name,
                portfolio_found=portfolio is not None,
                portfolio_path=portfolio.path if portfolio else None,
            )
        )
    return sections


def build_portfolio_index(source_root: Path, repository_root: Path) -> dict[str, PortfolioRecord]:
    portfolio_index: dict[str, PortfolioRecord] = {}
    for path in find_portfolios(source_root):
        record = PortfolioRecord(
            filename=path.name,
            path=relpath(path, repository_root),
            sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
            release_version=infer_release_version(path.name),
        )
        portfolio_index[path.name.lower()] = record
    return portfolio_index


def build_kb_document_record(
    html_path: Path,
    *,
    source_root: Path,
    repository_root: Path,
    portfolio_by_name: dict[str, PortfolioRecord],
) -> KbDocumentRecord:
    raw_html = read_text_lossy(html_path)
    page_text = normalize_text(raw_html)
    referenced_names = extract_referenced_portfolio_filenames(raw_html, page_text)

    warnings: list[str] = []
    if not referenced_names:
        warnings.append("No PDF portfolio references were detected in this KB HTML source.")

    referenced_records: list[ReferencedPortfolioRecord] = []
    for filename in referenced_names:
        portfolio = portfolio_by_name.get(filename.lower())
        referenced_records.append(
            ReferencedPortfolioRecord(
                filename=filename,
                found=portfolio is not None,
                path=portfolio.path if portfolio else None,
                sha256=portfolio.sha256 if portfolio else None,
                size_bytes=portfolio.size_bytes if portfolio else None,
                release_version=portfolio.release_version if portfolio else infer_release_version(filename),
            )
        )

    return KbDocumentRecord(
        kb_document_id=extract_kb_document_id(raw_html, html_path),
        source_html=relpath(html_path, repository_root),
        source_html_sha256=sha256_file(html_path),
        source_html_size_bytes=html_path.stat().st_size,
        maintenance_pack=infer_maintenance_pack(html_path, page_text),
        referenced_portfolios=referenced_records,
        hot_fix_sections=extract_hot_fix_sections(page_text, portfolio_by_name),
        extraction_warnings=warnings,
    )


def flatten_referenced_filenames(kb_documents: Iterable[KbDocumentRecord]) -> set[str]:
    referenced: set[str] = set()
    for document in kb_documents:
        for portfolio in document.referenced_portfolios:
            referenced.add(portfolio.filename.lower())
    return referenced


def build_manifest(source_root: Path, output_path: Path) -> SourceInventoryManifest:
    repository_root = repo_root()
    resolved_source_root = source_root.resolve()
    portfolio_by_name = build_portfolio_index(resolved_source_root, repository_root)
    html_sources = find_html_sources(resolved_source_root)

    warnings: list[str] = []
    if not html_sources:
        warnings.append(f"No KB HTML sources found under {source_root}.")
    if not portfolio_by_name:
        warnings.append(f"No PDF portfolio files found under {source_root}.")

    kb_documents = [
        build_kb_document_record(
            html_path,
            source_root=resolved_source_root,
            repository_root=repository_root,
            portfolio_by_name=portfolio_by_name,
        )
        for html_path in html_sources
    ]

    referenced_names = flatten_referenced_filenames(kb_documents)
    missing_portfolios = sorted(
        {
            portfolio.filename
            for document in kb_documents
            for portfolio in document.referenced_portfolios
            if not portfolio.found
        },
        key=str.lower,
    )
    unreferenced_portfolios = sorted(
        (
            portfolio
            for key, portfolio in portfolio_by_name.items()
            if key not in referenced_names
        ),
        key=lambda record: record.filename.lower(),
    )

    return SourceInventoryManifest(
        manifest_type="kb_source_inventory.v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        source_root=relpath(resolved_source_root, repository_root),
        html_source_count=len(html_sources),
        portfolio_file_count=len(portfolio_by_name),
        kb_documents=kb_documents,
        unreferenced_portfolios=unreferenced_portfolios,
        missing_portfolios=missing_portfolios,
        warnings=warnings,
    )


def write_manifest(manifest: SourceInventoryManifest, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Build a Gate 1 source inventory manifest for downloaded KB HTML and PDF portfolios."
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=root / "kbs",
        help="Directory containing KB HTML files and PDF portfolio files. Defaults to <repo>/kbs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "manifests" / "source_inventory.json",
        help="Manifest JSON output path. Defaults to <repo>/kbs/manifests/source_inventory.json.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_manifest(args.source_root, args.output)
    write_manifest(manifest, args.output)

    print(f"Wrote source inventory manifest: {args.output}")
    print(f"KB HTML sources: {manifest.html_source_count}")
    print(f"Portfolio files: {manifest.portfolio_file_count}")
    print(f"Missing referenced portfolios: {len(manifest.missing_portfolios)}")
    print(f"Unreferenced portfolio files: {len(manifest.unreferenced_portfolios)}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pypdf import PdfReader

PORTFOLIO_FILENAME_RE = re.compile(r"[A-Za-z0-9_.-]+_PFDs_Portfolio\.pdf", re.IGNORECASE)
SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
FIX_IDENTIFIER_RE = re.compile(r"(?:^|[_\s-])(?P<kind>Bug|Enh)[_\s-]+(?P<number>\d{5,})(?:$|[_\s.-])", re.IGNORECASE)


@dataclass(frozen=True)
class ExtractedAttachmentRecord:
    parent_portfolio_file: str
    parent_portfolio_path: str
    child_original_filename: str
    child_output_filename: str
    child_output_path: str
    child_sha256: str
    child_size_bytes: int
    content_type: str | None
    candidate_fix_type: str | None
    candidate_fix_number: str | None
    candidate_fix_identifier: str | None
    extraction_status: str
    extraction_error: str | None = None


@dataclass(frozen=True)
class PortfolioExtractionRecord:
    parent_portfolio_file: str
    parent_portfolio_path: str
    parent_sha256: str
    parent_size_bytes: int
    output_directory: str
    embedded_file_count: int
    extracted_file_count: int
    candidate_fix_identifier_count: int
    extraction_status: str
    extraction_error: str | None
    extracted_attachments: list[ExtractedAttachmentRecord] = field(default_factory=list)


@dataclass(frozen=True)
class PortfolioExtractionManifest:
    manifest_type: str
    generated_utc: str
    source_inventory_path: str
    extraction_root: str
    portfolio_count: int
    extracted_attachment_count: int
    candidate_fix_identifier_count: int
    failed_portfolio_count: int
    portfolios: list[PortfolioExtractionRecord]
    warnings: list[str]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def safe_filename(filename: str, fallback: str) -> str:
    base = Path(filename).name.strip() or fallback
    safe = SAFE_FILENAME_RE.sub("_", base).strip("._")
    return safe or fallback


def extract_candidate_fix_identifier(filename: str) -> tuple[str | None, str | None, str | None]:
    match = FIX_IDENTIFIER_RE.search(filename)
    if not match:
        return None, None, None

    raw_kind = match.group("kind").lower()
    fix_type = "BUG" if raw_kind == "bug" else "ENHANCEMENT"
    fix_number = match.group("number")
    return fix_type, fix_number, f"{fix_type}:{fix_number}"


def unique_output_path(output_dir: Path, requested_name: str) -> Path:
    candidate = output_dir / requested_name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 2
    while True:
        numbered = output_dir / f"{stem}_{counter}{suffix}"
        if not numbered.exists():
            return numbered
        counter += 1


def read_source_inventory(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def portfolio_paths_from_inventory(inventory: dict[str, Any], repository_root: Path) -> list[Path]:
    paths: dict[str, Path] = {}
    for document in inventory.get("kb_documents", []):
        for portfolio in document.get("referenced_portfolios", []):
            raw_path = portfolio.get("path")
            if raw_path:
                path = repository_root / raw_path
                paths[path.name.lower()] = path
    return sorted(paths.values(), key=lambda path: path.name.lower())


def read_embedded_files(reader: PdfReader) -> list[tuple[str, bytes, str | None]]:
    attachments: list[tuple[str, bytes, str | None]] = []
    attachment_map = getattr(reader, "attachments", {})

    for filename, payloads in attachment_map.items():
        if isinstance(payloads, (bytes, bytearray)):
            payload_list = [bytes(payloads)]
        else:
            payload_list = [bytes(payload) for payload in payloads]

        for index, payload in enumerate(payload_list, start=1):
            effective_name = filename
            if len(payload_list) > 1:
                path = Path(filename)
                effective_name = f"{path.stem}_{index}{path.suffix}"
            attachments.append((effective_name, payload, None))

    return attachments


def extract_portfolio(
    portfolio_path: Path,
    *,
    extraction_root: Path,
    repository_root: Path,
) -> PortfolioExtractionRecord:
    parent_sha256 = sha256_file(portfolio_path)
    parent_size = portfolio_path.stat().st_size
    output_dir = extraction_root / portfolio_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        reader = PdfReader(str(portfolio_path))
        embedded_files = read_embedded_files(reader)
    except Exception as exc:  # noqa: BLE001 - record portfolio-level extraction failure.
        return PortfolioExtractionRecord(
            parent_portfolio_file=portfolio_path.name,
            parent_portfolio_path=relpath(portfolio_path, repository_root),
            parent_sha256=parent_sha256,
            parent_size_bytes=parent_size,
            output_directory=relpath(output_dir, repository_root),
            embedded_file_count=0,
            extracted_file_count=0,
            candidate_fix_identifier_count=0,
            extraction_status="FAILED",
            extraction_error=str(exc),
            extracted_attachments=[],
        )

    extracted: list[ExtractedAttachmentRecord] = []
    for index, (original_filename, payload, content_type) in enumerate(embedded_files, start=1):
        fallback_name = f"attachment_{index:03d}.pdf"
        output_name = safe_filename(original_filename, fallback=fallback_name)
        output_path = unique_output_path(output_dir, output_name)
        fix_type, fix_number, fix_identifier = extract_candidate_fix_identifier(output_name)

        try:
            output_path.write_bytes(payload)
            status = "EXTRACTED"
            error = None
            child_hash = sha256_bytes(payload)
            child_size = len(payload)
        except Exception as exc:  # noqa: BLE001 - record child-level extraction failure.
            status = "FAILED"
            error = str(exc)
            child_hash = ""
            child_size = 0

        extracted.append(
            ExtractedAttachmentRecord(
                parent_portfolio_file=portfolio_path.name,
                parent_portfolio_path=relpath(portfolio_path, repository_root),
                child_original_filename=original_filename,
                child_output_filename=output_path.name,
                child_output_path=relpath(output_path, repository_root),
                child_sha256=child_hash,
                child_size_bytes=child_size,
                content_type=content_type,
                candidate_fix_type=fix_type,
                candidate_fix_number=fix_number,
                candidate_fix_identifier=fix_identifier,
                extraction_status=status,
                extraction_error=error,
            )
        )

    successful_count = sum(1 for item in extracted if item.extraction_status == "EXTRACTED")
    candidate_fix_count = sum(1 for item in extracted if item.candidate_fix_identifier is not None)
    if not embedded_files:
        status = "NO_EMBEDDED_FILES"
    elif successful_count == len(embedded_files):
        status = "EXTRACTED"
    elif successful_count > 0:
        status = "PARTIAL"
    else:
        status = "FAILED"

    return PortfolioExtractionRecord(
        parent_portfolio_file=portfolio_path.name,
        parent_portfolio_path=relpath(portfolio_path, repository_root),
        parent_sha256=parent_sha256,
        parent_size_bytes=parent_size,
        output_directory=relpath(output_dir, repository_root),
        embedded_file_count=len(embedded_files),
        extracted_file_count=successful_count,
        candidate_fix_identifier_count=candidate_fix_count,
        extraction_status=status,
        extraction_error=None,
        extracted_attachments=extracted,
    )


def build_manifest(source_inventory_path: Path, extraction_root: Path) -> PortfolioExtractionManifest:
    repository_root = repo_root()
    inventory = read_source_inventory(source_inventory_path)
    portfolio_paths = portfolio_paths_from_inventory(inventory, repository_root)

    warnings: list[str] = []
    if not portfolio_paths:
        warnings.append("No portfolio paths were found in the source inventory manifest.")

    records = [
        extract_portfolio(
            portfolio_path,
            extraction_root=extraction_root,
            repository_root=repository_root,
        )
        for portfolio_path in portfolio_paths
    ]

    return PortfolioExtractionManifest(
        manifest_type="pdf_portfolio_extraction.v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        source_inventory_path=relpath(source_inventory_path, repository_root),
        extraction_root=relpath(extraction_root, repository_root),
        portfolio_count=len(records),
        extracted_attachment_count=sum(record.extracted_file_count for record in records),
        candidate_fix_identifier_count=sum(record.candidate_fix_identifier_count for record in records),
        failed_portfolio_count=sum(1 for record in records if record.extraction_status == "FAILED"),
        portfolios=records,
        warnings=warnings,
    )


def write_manifest(manifest: PortfolioExtractionManifest, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Extract embedded PDFs/files from PDF Portfolio documents referenced by the KB source inventory manifest."
    )
    parser.add_argument(
        "--source-inventory",
        type=Path,
        default=root / "kbs" / "manifests" / "source_inventory.json",
        help="Path to source_inventory.json generated by extract_kb_source_manifest.py.",
    )
    parser.add_argument(
        "--extraction-root",
        type=Path,
        default=root / "kbs" / "extracted",
        help="Directory where extracted portfolio children should be written.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "manifests" / "portfolio_extraction.json",
        help="Portfolio extraction manifest output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.extraction_root.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(args.source_inventory, args.extraction_root)
    write_manifest(manifest, args.output)

    print(f"Wrote portfolio extraction manifest: {args.output}")
    print(f"Portfolio files processed: {manifest.portfolio_count}")
    print(f"Extracted attachments: {manifest.extracted_attachment_count}")
    print(f"Candidate fix identifiers: {manifest.candidate_fix_identifier_count}")
    print(f"Failed portfolios: {manifest.failed_portfolio_count}")


if __name__ == "__main__":
    main()

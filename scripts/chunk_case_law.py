"""Chunk processed case-law judgment text, preserving paragraph structure."""

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.case_law import CASE_METADATA, validate_case_metadata  # noqa: E402
from scripts.chunk import chunk_text  # noqa: E402

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CASE_LAW_PROCESSED_DIR = PROCESSED_DIR / "case_law"
CHUNKS_DIR = PROCESSED_DIR / "chunks" / "case_law"
METADATA_DIR = PROCESSED_DIR / "metadata" / "case_law"

# A standard Supreme Court judgment paragraph: a line starting with a
# paragraph number followed by a period and a space, e.g. "13. This leads".
PARAGRAPH_PATTERN = re.compile(r"(?m)^\s*(\d{1,4})\.\s+")

# Judgment exports commonly mark opinion sections with short all-caps or
# title-case headings. Keep only headings that occupy their own line and avoid
# treating long prose lines as section labels.
SECTION_PATTERN = re.compile(
	r"(?m)^\s*([A-Z][A-Z0-9 ,&'()/-]{2,80}|[A-Z][A-Za-z0-9 ,&'()/-]{2,80})\s*$"
)

# A genuinely paragraph-numbered judgment keeps paragraphs page-sized or
# smaller throughout. Older scans (e.g. Maneka Gandhi's 1978 JUDIS text) only
# number a short headnote summary and then run on as unnumbered prose for the
# rest of the opinion — matching against that headnote alone would merge the
# entire remaining judgment into one oversized "paragraph". Treating any
# split with an oversized paragraph as unreliable and falling back to fixed
# windows catches that case.
MAX_PARAGRAPH_CHARS = 6000

# CASE_METADATA now lives in backend/case_law.py (single source of truth
# shared with backend/api/routes/sources.py's related_cases lookup).


def split_by_paragraph_number(text: str) -> list[str]:
	"""Split judgment text on numbered paragraph markers, if present."""
	matches = list(PARAGRAPH_PATTERN.finditer(text))
	if len(matches) < 3:
		return []
	paragraphs = []
	for index, match in enumerate(matches):
		start = match.start()
		end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
		paragraph = text[start:end].strip()
		if paragraph:
			paragraphs.append(paragraph)
	if any(len(paragraph) > MAX_PARAGRAPH_CHARS for paragraph in paragraphs):
		return []
	return paragraphs


def chunk_case_text(text: str) -> list[str]:
	"""Chunk judgment text by numbered paragraph, falling back to sections/windows."""
	return [chunk for _, chunk in chunk_case_sections(text)]


def chunk_case_sections(text: str) -> list[tuple[str | None, str]]:
	"""Return chunks paired with the section context they belong to."""
	section_spans = _section_spans(text)
	paragraphs = split_by_paragraph_number(text)
	if paragraphs:
		return [
			(_section_at_offset(text.find(paragraph), section_spans), paragraph)
			for paragraph in paragraphs
		]

	sections = _split_by_section(text)
	if len(sections) > 1:
		chunks = []
		for section in sections:
			section_name = section_for_chunk(section)
			chunks.extend((section_name, chunk) for _, chunk in chunk_text(section))
		return chunks
	return [(None, chunk) for _, chunk in chunk_text(text)]


def _section_spans(text: str) -> list[tuple[int, str]]:
	"""Return heading offsets so numbered paragraphs inherit section context."""
	return [(match.start(), match.group(1).strip()) for match in SECTION_PATTERN.finditer(text)]


def _section_at_offset(offset: int, spans: list[tuple[int, str]]) -> str | None:
	current = None
	for heading_offset, heading in spans:
		if heading_offset > offset:
			break
		current = heading
	return current


def _split_by_section(text: str) -> list[str]:
	"""Split unnumbered judgment text at standalone opinion headings."""
	matches = list(SECTION_PATTERN.finditer(text))
	if len(matches) < 2:
		return []
	sections = []
	start = 0
	for match in matches:
		if match.start() > start:
			section = text[start:match.start()].strip()
			if section:
				sections.append(section)
		start = match.start()
	last_section = text[start:].strip()
	if last_section:
		sections.append(last_section)
	return sections


def section_for_chunk(text: str) -> str | None:
	"""Return the leading standalone heading, when a chunk starts in one."""
	match = SECTION_PATTERN.match(text)
	return match.group(1).strip() if match else None


def case_metadata_for(case_id: str) -> dict:
	"""Return the known case metadata for a slug, or a flagged placeholder."""
	if case_id in CASE_METADATA:
		return dict(CASE_METADATA[case_id])
	return {
		"case_name": None,
		"case_citation": None,
		"date": None,
		"year": None,
		"court": None,
		"document_type": None,
		"source_file": None,
	}


def _metadata_for_chunk(case_id: str, chunk_index: int, chunk_text: str = "") -> dict:
	"""Build the Section 5 case-law metadata shape for one chunk."""
	case_info = case_metadata_for(case_id)
	warnings = validate_case_metadata(case_id, case_info)
	if case_info["case_name"] is None and not warnings:
		warnings.append(f"no case metadata registered for '{case_id}'")
	return {
		"case_id": case_id,
		"case_name": case_info["case_name"],
		"case_citation": case_info.get("case_citation"),
		"date": case_info.get("date", case_info.get("year")),
		"year": case_info["year"],
		"court": case_info["court"],
		"category": "constitutional_law",
		"document_type": "case_law",
		"source_type": "case_law",
		"language": "english",
		"source_file": case_info.get("source_file", f"{case_id}.pdf"),
		"section": section_for_chunk(chunk_text),
		"metadata_extraction_failed": bool(warnings),
		"metadata_warnings": warnings,
	}


def process_case_file(source_path: Path) -> tuple[Path, Path, int]:
	"""Chunk one processed case-law text file and write chunk/metadata JSONL."""
	text = source_path.read_text(encoding="utf-8")
	case_id = source_path.stem
	metadata_issues = validate_case_metadata(case_id, case_metadata_for(case_id))
	if metadata_issues:
		raise ValueError("Cannot chunk case-law file: " + "; ".join(metadata_issues))
	chunk_path = (CHUNKS_DIR / source_path.name).with_suffix(".jsonl")
	metadata_path = (METADATA_DIR / source_path.name).with_suffix(".jsonl")
	chunk_path.parent.mkdir(parents=True, exist_ok=True)
	metadata_path.parent.mkdir(parents=True, exist_ok=True)

	chunk_records = []
	metadata_records = []
	for index, (section, chunk) in enumerate(chunk_case_sections(text)):
		chunk_records.append({"chunk_id": index, "text": chunk})
		metadata_records.append(
			{
				"chunk_id": index,
				**_metadata_for_chunk(case_id, index, chunk),
				"section": section,
			}
		)

	chunk_path.write_text(
		"\n".join(json.dumps(record, ensure_ascii=True) for record in chunk_records) + "\n",
		encoding="utf-8",
	)
	metadata_path.write_text(
		"\n".join(json.dumps(record, ensure_ascii=True) for record in metadata_records) + "\n",
		encoding="utf-8",
	)
	return chunk_path, metadata_path, len(chunk_records)


def main() -> None:
	"""Chunk every processed case-law text file below data/processed/case_law/."""
	parser = argparse.ArgumentParser(description=__doc__)
	parser.parse_args()
	CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
	METADATA_DIR.mkdir(parents=True, exist_ok=True)
	text_files = sorted(CASE_LAW_PROCESSED_DIR.glob("*.txt"))
	for source_path in text_files:
		chunk_path, metadata_path, count = process_case_file(source_path)
		print(f"Chunked {source_path} -> {chunk_path} and {metadata_path} ({count} chunks)")
	if not text_files:
		print(f"No processed case-law text files found in {CASE_LAW_PROCESSED_DIR}")


if __name__ == "__main__":
	main()

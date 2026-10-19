"""Audit processed judgments for required legal sections and metadata integrity."""

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.case_law import CASE_METADATA, validate_case_metadata

CASE_LAW_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "case_law"
CASE_LAW_METADATA_DIR = PROJECT_ROOT / "data" / "processed" / "metadata" / "case_law"
CASE_LAW_CHUNKS_DIR = PROJECT_ROOT / "data" / "processed" / "chunks" / "case_law"

SECTION_PATTERNS = {
	"facts": re.compile(r"\b(facts?|background|brief facts|factual matrix)\b", re.I),
	"issues": re.compile(r"\b(issues?|questions? for determination|points? for determination)\b", re.I),
	"arguments": re.compile(r"\b(arguments?|submissions?|contentions?|pleadings?)\b", re.I),
	"reasoning": re.compile(r"\b(reasoning|analysis|discussion|consideration|findings?)\b", re.I),
	"holding": re.compile(r"\b(judgment|judgement|holding|held that|conclusion|disposition|order)\b", re.I),
	"separate_opinions": re.compile(r"\b(separate opinion|dissenting opinion|concurring opinion|dissent|concurrence)\b", re.I),
}


def audit_case(case_id: str, text: str, metadata_path: Path | None = None, chunk_path: Path | None = None) -> dict:
	"""Return missing required sections and metadata problems for one case."""
	metadata = CASE_METADATA.get(case_id)
	metadata_issues = (
		[f"case not registered: {case_id}"]
		if metadata is None
		else validate_case_metadata(case_id, metadata)
	)
	chunk_issues = []
	if metadata_path and chunk_path and metadata_path.exists() and chunk_path.exists():
		metadata = [json.loads(line) for line in metadata_path.read_text(encoding="utf-8").splitlines()]
		chunks = [json.loads(line) for line in chunk_path.read_text(encoding="utf-8").splitlines()]
		if len(metadata) != len(chunks):
			chunk_issues.append("chunk/metadata count mismatch")
		for record in metadata:
			if record.get("case_id") != case_id:
				chunk_issues.append(f"chunk {record.get('chunk_id')} has wrong case_id")
			if record.get("case_name") != (metadata and CASE_METADATA.get(case_id, {}).get("case_name")):
				chunk_issues.append(f"chunk {record.get('chunk_id')} has wrong case_name")
			if record.get("document_type") != "case_law":
				chunk_issues.append(f"chunk {record.get('chunk_id')} has wrong document_type")
	sections = {
		name: bool(pattern.search(text))
		for name, pattern in SECTION_PATTERNS.items()
	}
	return {
		"case_id": case_id,
		"metadata_issues": metadata_issues,
		"chunk_issues": sorted(set(chunk_issues)),
		"sections": sections,
		"missing_sections": [
			name for name, present in sections.items()
			if not present and name != "separate_opinions"
		],
		"missing_optional_sections": [
			"separate_opinions"
			for present in [sections["separate_opinions"]]
			if not present
		],
	}


def audit_all(directory: Path = CASE_LAW_PROCESSED_DIR) -> list[dict]:
	"""Audit every processed case-law text file in a directory."""
	reports = []
	for path in sorted(directory.glob("*.txt")):
		case_id = path.stem
		reports.append(
			audit_case(
				case_id,
				path.read_text(encoding="utf-8"),
				CASE_LAW_METADATA_DIR / f"{case_id}.jsonl",
				CASE_LAW_CHUNKS_DIR / f"{case_id}.jsonl",
			)
		)
	return reports


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--strict", action="store_true", help="exit non-zero when anything is missing")
	args = parser.parse_args()
	reports = audit_all()
	for report in reports:
		missing = ", ".join(report["missing_sections"]) or "none"
		optional = ", ".join(report["missing_optional_sections"]) or "none"
		metadata = ", ".join(report["metadata_issues"] + report["chunk_issues"]) or "none"
		print(f"{report['case_id']}: missing sections=[{missing}] optional sections=[{optional}] metadata=[{metadata}]")
	if args.strict and any(report["missing_sections"] or report["metadata_issues"] or report["chunk_issues"] for report in reports):
		raise SystemExit(1)


if __name__ == "__main__":
	main()
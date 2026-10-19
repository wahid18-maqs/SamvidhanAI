"""Embed processed chunks and upsert them into Pinecone."""

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import PINECONE_NAMESPACE
from backend.case_law import validate_case_metadata
from backend.services.pinecone import PineconeService

CHUNKS_DIR = PROJECT_ROOT / "data" / "processed" / "chunks"
METADATA_DIR = PROJECT_ROOT / "data" / "processed" / "metadata"
# Must match backend.config.PINECONE_NAMESPACE — that's the namespace
# PineconeRetriever actually queries at request time. A hardcoded default
# here that drifts from config silently indexes into a namespace retrieval
# never reads from.
DEFAULT_NAMESPACE = PINECONE_NAMESPACE
UPSERT_BATCH_SIZE = 96
BATCH_DELAY_SECONDS = 3.0
MAX_RETRIES = 5


def _upsert_with_retry(service, batch, namespace):
	"""Upsert one batch, backing off on the integrated-embedder's rate limit."""
	from pinecone.openapi_support.exceptions import PineconeApiException

	for attempt in range(MAX_RETRIES):
		try:
			return service.upsert_records(batch, namespace=namespace)
		except PineconeApiException as exc:
			exc_text = str(exc)
			if "embedding token limit" in exc_text.lower():
				raise RuntimeError(
					"Pinecone embedding quota exhausted for the current month. "
					"Upgrade the organization, wait for the quota reset, or switch "
					"to precomputed embeddings before rerunning scripts/index.py."
				) from exc
			if exc.status != 429 or attempt == MAX_RETRIES - 1:
				raise
			wait = 20 * (attempt + 1)
			print(f"  rate limited, retrying in {wait}s (attempt {attempt + 1}/{MAX_RETRIES})")
			time.sleep(wait)


def _metadata_path(chunk_path: Path) -> Path:
	return METADATA_DIR / chunk_path.relative_to(CHUNKS_DIR)


def _load_records(chunk_path: Path) -> list[dict]:
	metadata_path = _metadata_path(chunk_path)
	if not metadata_path.exists():
		raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
	chunks = [json.loads(line) for line in chunk_path.read_text(encoding="utf-8").splitlines()]
	metadata = [json.loads(line) for line in metadata_path.read_text(encoding="utf-8").splitlines()]
	metadata_by_id = {record["chunk_id"]: record for record in metadata}
	if len(metadata_by_id) != len(metadata) or len(chunks) != len(metadata):
		raise ValueError(f"Chunk/metadata count mismatch for {chunk_path}")
	case_records = [record for record in metadata if record.get("document_type") == "case_law"]
	if case_records:
		case_ids = {record.get("case_id") for record in case_records}
		if len(case_ids) != 1 or None in case_ids:
			raise ValueError(f"Case metadata identity mismatch for {chunk_path}")
		case_id = next(iter(case_ids))
		for record in case_records:
			issues = validate_case_metadata(case_id, record)
			if record.get("metadata_extraction_failed") or issues:
				raise ValueError(
					f"Invalid case metadata for {chunk_path} chunk {record.get('chunk_id')}: "
					+ "; ".join(record.get("metadata_warnings", []) + issues)
				)
	return [
		{"chunk": chunk, "metadata": metadata_by_id[chunk["chunk_id"]]}
		for chunk in chunks
	]


def _pinecone_metadata(metadata: dict) -> dict:
	"""Remove nulls while retaining populated schema fields and review flags."""
	return {key: value for key, value in metadata.items() if value is not None}


def _build_records(records: list[dict], source_name: str) -> list[dict]:
	"""Build Pinecone text records for server-side integrated embedding."""
	return [
		{
			"_id": f"{source_name}:{record['chunk']['chunk_id']}",
			"text": record["chunk"]["text"],
			**_pinecone_metadata(record["metadata"]),
		}
		for record in records
	]


def index_chunks(dry_run: bool = False, namespace: str = DEFAULT_NAMESPACE) -> int:
	"""Embed every chunk and optionally upsert the resulting vectors."""
	chunk_files = sorted(CHUNKS_DIR.rglob("*.jsonl"))
	if not chunk_files:
		print(f"No chunk files found in {CHUNKS_DIR}")
		return 0
	service = None if dry_run else PineconeService()
	total = 0
	for chunk_path in chunk_files:
		relative_source = str(chunk_path.relative_to(CHUNKS_DIR).with_suffix(""))
		records = _build_records(_load_records(chunk_path), relative_source)
		if service:
			batches = range(0, len(records), UPSERT_BATCH_SIZE)
			for batch_index, start in enumerate(batches):
				_upsert_with_retry(
					service, records[start:start + UPSERT_BATCH_SIZE], namespace
				)
				print(f"  upserted batch {batch_index + 1} ({min(start + UPSERT_BATCH_SIZE, len(records))}/{len(records)})")
				time.sleep(BATCH_DELAY_SECONDS)
		total += len(records)
		print(f"Prepared {len(records)} records from {chunk_path}")
	print(f"{'Dry run prepared' if dry_run else 'Upserted'} {total} records")
	return total


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--dry-run", action="store_true", help="embed and validate without Pinecone writes")
	parser.add_argument("--namespace", default=DEFAULT_NAMESPACE)
	args = parser.parse_args()
	index_chunks(dry_run=args.dry_run, namespace=args.namespace)


if __name__ == "__main__":
	main()

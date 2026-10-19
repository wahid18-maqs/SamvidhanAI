"""Source explorer route for ConstituteAI (Section 4/1.5).

Anonymous access is fine here — Section 8.2 lists read-only reference
lookups as not needing an account.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

from backend.case_law import CASE_METADATA
from backend.config import PINECONE_NAMESPACE
from backend.models.source import SourceResponse
from backend.rag.retriever import is_embedding_quota_error
from backend.services.pinecone import PineconeService
from backend.services.pinecone_chat import hits_from_response

router = APIRouter()

_service = None


def _related_cases_for_article(article: str) -> list[str]:
	"""Reverse-lookup: which indexed cases' related_articles include this
	article? Powers the Source Explorer's "Landmark judgments" section
	(Ui updates and features.md 1.6) for constitutional-text sources."""
	return [
		f"{meta['case_name']} ({meta['year']})"
		for meta in CASE_METADATA.values()
		if article in meta.get("related_articles", [])
	]


def _get_service() -> PineconeService:
	global _service
	if _service is None:
		_service = PineconeService()
	return _service


def _build_source_response(source_id: str) -> Optional[SourceResponse]:
	"""Shared lookup used by both the single-source route below and the
	multi-article /api/articles route (Ui updates and features.md 2.2 A1) —
	returns None on no match instead of raising, so a category lookup can
	skip a missing article rather than fail wholesale."""
	if source_id.startswith("article_"):
		article = source_id.removeprefix("article_")
		metadata_filter = {"article": {"$eq": article}, "document_type": {"$eq": "constitution"}}
		query_text = f"Article {article}"
	else:
		metadata_filter = {"case_id": {"$eq": source_id}, "document_type": {"$eq": "case_law"}}
		query_text = source_id.replace("_", " ")

	try:
		response = _get_service().search_text(
			text=query_text, top_k=5, filter=metadata_filter, namespace=PINECONE_NAMESPACE
		)
	except Exception as error:
		if not is_embedding_quota_error(error):
			raise
		return None
	hits = hits_from_response(response)
	if not hits:
		return None

	fields = hits[0].get("fields", {})
	combined_text = "\n\n".join(hit.get("fields", {}).get("text", "") for hit in hits)
	article_number = fields.get("article")

	return SourceResponse(
		source_id=source_id,
		article=article_number,
		clause=fields.get("clause"),
		original_text=combined_text,
		document=fields.get("case_name") or "Constitution of India",
		page=int(fields["page"]) if fields.get("page") is not None else None,
		source_type=fields.get("source_type") or fields.get("category") or "unknown",
		related_provisions=[],
		related_cases=_related_cases_for_article(article_number) if article_number else [],
	)


@router.get("/api/source/{source_id}", response_model=SourceResponse)
def get_source(source_id: str):
	source = _build_source_response(source_id)
	if source is None:
		raise HTTPException(status_code=404, detail="Source not found")
	return source

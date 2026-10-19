"""Metadata builder node: combines intent with the analyzer's regex filter."""

from backend.case_law import CASE_METADATA
from backend.graph.state import GraphState

# Section 6 routing table: which document_type an intent should search.
# "history"/"general" deliberately search both constitutional text and case
# law, per the spec ("General Query -> text + case-law retrieval").
_DOCUMENT_TYPE_BY_INTENT = {
	"article": "constitution",
	"amendment": "constitution",
	"case_law": "case_law",
}


def build_metadata_filter(state: GraphState) -> GraphState:
	"""Layer an intent-driven document_type constraint onto the base filter."""
	metadata_filter = dict(state.get("metadata_filter") or {})
	intent = state.get("intent", "general")
	document_type = _DOCUMENT_TYPE_BY_INTENT.get(intent)
	if intent == "case_law":
		# article/clause are constitution-only fields; case-law chunks never
		# carry them, so keeping them here would zero out every match.
		metadata_filter.pop("article", None)
		metadata_filter.pop("clause", None)
		# When analyze_query resolved the query to exactly one known case,
		# narrow the search to that case's own vectors rather than letting a
		# large judgment on the same doctrine crowd a smaller one out of the
		# top-K by embedding similarity alone (see ingestion.md). No
		# resolved_case_id means either no case was named, more than one
		# was, or the match wasn't confident -- all three fall back to
		# searching the whole case-law corpus, same as before this filter
		# existed.
		resolved_case_id = state.get("resolved_case_id")
		if resolved_case_id:
			metadata_filter["case_id"] = {"$eq": resolved_case_id}
			case_name = CASE_METADATA.get(resolved_case_id, {}).get("case_name")
			if case_name:
				metadata_filter["case_name"] = {"$eq": case_name}
	if document_type:
		metadata_filter["document_type"] = {"$eq": document_type}
	return {**state, "metadata_filter": metadata_filter or None}

"""Citation builder node: derives source citations from retrieved hits."""

from typing import Optional

from backend.graph.state import GraphState


def citation_for(metadata: dict) -> Optional[dict]:
	"""Derive {source_id, label} from one chunk's metadata, or None if this
	metadata doesn't identify a citable source. Shared by the retrieval
	node (to label context for the model) and the citation-resolution step
	in generation (to validate what the model actually cited)."""
	article = metadata.get("article")
	source_id = metadata.get("source_id")
	label = metadata.get("label")
	if metadata.get("document_type") == "case_law":
		source_id = metadata.get("case_id") or source_id
		case_name = metadata.get("case_name") or label
		case_citation = metadata.get("case_citation")
		label = f"{case_name} ({case_citation})" if case_citation else case_name
	elif article:
		source_id = f"article_{article}"
		label = label or f"Article {article}"
	if not source_id:
		return None
	return {"source_id": str(source_id), "label": str(label or source_id)}


def build_citations(state: GraphState) -> GraphState:
	"""Build the deduplicated flat citation list from what the model
	actually cited in its sections/key_clauses — not blindly from every
	retrieved chunk, so a source retrieval turned up but the model never
	used doesn't show up as if it were used."""
	citations = []
	seen = set()
	for piece in (state.get("sections") or []) + (state.get("key_clauses") or []):
		for citation in piece.get("citations") or []:
			source_id = citation.get("source_id")
			if source_id and source_id not in seen:
				citations.append(citation)
				seen.add(source_id)
	return {**state, "citations": citations}

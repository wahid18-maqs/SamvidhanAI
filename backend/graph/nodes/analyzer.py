"""Query analyzer node: deterministic intent classification + reference extraction."""

import re

from backend.case_law import resolve_single_case_id
from backend.graph.state import GraphState
from backend.rag.retriever import extract_metadata_filter
from scripts.chunk_case_law import CASE_METADATA

AMENDMENT_PATTERN = re.compile(r"\bamend(ment|ed|ing)?\b", re.IGNORECASE)
HISTORY_PATTERN = re.compile(
	r"\b(history|adopted|drafted|drafting|constituent assembly|enacted|came into (force|effect))\b",
	re.IGNORECASE,
)
CASE_LAW_PATTERN = re.compile(r"\b(v\.?s?\.?|versus|judgment|judgement|case|verdict|ruling)\b", re.IGNORECASE)

# Landmark cases named in the product spec (instructions_refactor.md Section
# 2.5) — used for intent classification even before a case is indexed, so
# routing is forward-compatible as the case-law corpus grows. Petitioner
# surname/short form is enough to catch a bare case-name mention with no
# "v."/"case"/"judgment" keyword nearby (e.g. "Explain Kesavananda Bharati.").
_LANDMARK_CASE_NAME_FRAGMENTS = [
	"kesavananda bharati",
	"maneka gandhi",
	"minerva mills",
	"golaknath",
	"s.r. bommai",
	"sr bommai",
	"puttaswamy",
	"shreya singhal",
]

# Case names from the registered/indexed case-law corpus, e.g. "maneka
# gandhi" from "maneka_gandhi_1978" — kept in sync with what's actually
# retrievable, in addition to the broader landmark list above.
_KNOWN_CASE_NAME_FRAGMENTS = list({
	*_LANDMARK_CASE_NAME_FRAGMENTS,
	*(info["case_name"].split(" v.")[0].lower() for info in CASE_METADATA.values()),
})


def _matches_known_case(query: str) -> bool:
	lowered = query.lower()
	return any(fragment in lowered for fragment in _KNOWN_CASE_NAME_FRAGMENTS)


def classify_intent(query: str, metadata_filter: dict) -> str:
	"""Classify a query into one of the 5 routing targets from Section 6."""
	if _matches_known_case(query) or CASE_LAW_PATTERN.search(query):
		return "case_law"
	if metadata_filter.get("article", {}).get("$eq") == "368" or AMENDMENT_PATTERN.search(query):
		return "amendment"
	if metadata_filter.get("article"):
		return "article"
	if HISTORY_PATTERN.search(query):
		return "history"
	return "general"


def analyze_query(state: GraphState) -> GraphState:
	"""Extract article/clause references and classify query intent."""
	query = state["query"]
	metadata_filter = extract_metadata_filter(query)
	intent = classify_intent(query, metadata_filter)
	return {
		**state,
		"original_query": state.get("original_query", query),
		"metadata_filter": metadata_filter or None,
		"intent": intent,
		"resolved_case_id": resolve_single_case_id(query),
		"retry_count": state.get("retry_count", 0),
	}

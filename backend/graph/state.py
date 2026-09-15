"""LangGraph state for the ConstituteAI retrieval/generation workflow."""

from typing import Any, Optional, TypedDict


class GraphState(TypedDict, total=False):
	"""Shared state threaded through every node in the chat workflow."""

	query: str
	original_query: str
	language: str
	chat_history: list[Any]
	intent: str  # "article" | "amendment" | "case_law" | "history" | "general"
	resolved_case_id: Optional[str]  # set only when a query names exactly one known case
	metadata_filter: Optional[dict]
	retrieved_documents: list[dict]
	context: str
	context_quality: str  # "good" | "weak"
	retry_count: int
	answer: str
	citations: list[dict]
	summary: str
	sections: list[dict]
	key_clauses: list[dict]
	explanation: str

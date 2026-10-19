"""Generation node: grounded, language-aware, structured Gemini answer generation."""

import logging
from typing import Any, Optional

from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field

from backend.config import GEMINI_API_KEY, GEMINI_MODEL
from backend.graph.nodes.citations import citation_for
from backend.graph.state import GraphState

logger = logging.getLogger(__name__)

DISCLAIMER = "This is a research aid, not legal advice."

# Section 6 generation constraints + Section 7.2 (retrieve English, answer in
# the user's language, keep citation labels untranslated) + Section 1.4's
# Summary/section/Key Clauses/Explanation structure.
SYSTEM_PROMPT = (
	"You are ConstituteAI, a constitutional research assistant for the "
	"Indian Constitution. The retrieved context below is made of passages, "
	"each preceded by its own \"[source_id: ...]\" tag. Ground every claim "
	"strictly in these passages. When you cite a source for a section or "
	"key clause, cite_source_ids must contain ONLY source_id values that "
	"literally appear as a [source_id: ...] tag above — never invent one, "
	"and never cite a source_id that isn't actually relevant to that "
	"specific piece of text. For case-law claims, include the retrieved "
	"case source_id so the backend can return its case name and citation. Distinguish constitutional text from case-law "
	"interpretation. If the context is insufficient to answer, say so "
	"explicitly in the summary and explanation, and leave sections and "
	"key_clauses empty rather than guessing. Keep article/clause "
	"identifiers and case names exactly as given in the context, never "
	"translated, even when answering in another language. Write the "
	"summary, section bodies, and explanation in {language_name}.\n\n"
	"Retrieved context:\n{context}"
)

# ISO code -> English name for every Eighth Schedule language in
# backend/models/chat.py's LanguageCode, plus English itself.
LANGUAGE_NAMES = {
	"en": "English", "as": "Assamese", "bn": "Bengali", "brx": "Bodo",
	"doi": "Dogri", "gu": "Gujarati", "hi": "Hindi", "kn": "Kannada",
	"ks": "Kashmiri", "kok": "Konkani", "mai": "Maithili", "ml": "Malayalam",
	"mni": "Manipuri", "mr": "Marathi", "ne": "Nepali", "or": "Odia",
	"pa": "Punjabi", "sa": "Sanskrit", "sat": "Santali", "sd": "Sindhi",
	"ta": "Tamil", "te": "Telugu", "ur": "Urdu",
}


class _RawSection(BaseModel):
	heading: str
	body: str
	cite_source_ids: list[str] = Field(default_factory=list)


class _RawKeyClause(BaseModel):
	text: str
	cite_source_ids: list[str] = Field(default_factory=list)


class _RawStructuredAnswer(BaseModel):
	"""The shape Gemini is asked to fill in directly. Citations are raw
	source_id strings here, not full label objects -- the model isn't
	trusted to also get the human-readable label right, only the backend's
	own retrieved metadata is (see generate_answer's resolution step)."""

	summary: str
	summary_cite_source_ids: list[str] = Field(default_factory=list)
	sections: list[_RawSection] = Field(default_factory=list)
	key_clauses: list[_RawKeyClause] = Field(default_factory=list)
	explanation: str


_model = None


def _get_model():
	global _model
	if _model is None:
		if not GEMINI_API_KEY:
			raise ValueError("GEMINI_API_KEY is required")
		from langchain_google_genai import ChatGoogleGenerativeAI

		_model = ChatGoogleGenerativeAI(
			model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY
		).with_structured_output(_RawStructuredAnswer)
	return _model


def build_prompt(state: GraphState) -> str:
	"""Assemble the full generation prompt for one turn."""
	language_name = LANGUAGE_NAMES.get(state.get("language", "en"), "English")
	system = SYSTEM_PROMPT.format(language_name=language_name, context=state.get("context", ""))
	history = "\n".join(
		f"{getattr(message, 'type', 'message')}: {getattr(message, 'content', message)}"
		for message in state.get("chat_history", [])
	)
	return f"{system}\n\nChat history:\n{history}\n\nQuestion: {state['query']}"


def _citation_lookup(retrieved_documents: list[dict]) -> dict[str, dict]:
	"""Map source_id -> {source_id, label} for every genuinely retrieved
	chunk, so a model-claimed source_id can be checked against reality."""
	lookup = {}
	for hit in retrieved_documents or []:
		citation = citation_for(hit.get("fields", {}))
		if citation:
			lookup[citation["source_id"]] = citation
	return lookup


def _resolve_citations(raw_source_ids: list[str], lookup: dict[str, dict]) -> list[dict]:
	"""Resolve model-claimed source_ids against what was actually
	retrieved, dropping (and logging) anything that doesn't match -- this
	is the actual anti-fabrication guarantee, not just a prompt instruction."""
	resolved = []
	for source_id in raw_source_ids:
		citation = lookup.get(source_id)
		if citation is None:
			logger.warning(
				"dropping unresolved model-claimed citation",
				extra={"structured": {"source_id": source_id}},
			)
			continue
		resolved.append(citation)
	return resolved


def _render_answer(structured: dict) -> str:
	"""Flatten the structured pieces into plain text, for the backward-
	compatible `answer` field."""
	parts = []
	if structured["summary"]:
		summary = structured["summary"]
		if structured.get("summary_citations"):
			labels = ", ".join(citation["label"] for citation in structured["summary_citations"])
			summary += f" ({labels})"
		parts.append(f"Summary: {summary}")
	for section in structured["sections"]:
		parts.append(f"{section['heading']}\n{section['body']}")
	if structured["key_clauses"]:
		parts.append(
			"Key Clauses:\n" + "\n".join(f"- {clause['text']}" for clause in structured["key_clauses"])
		)
	if structured["explanation"]:
		parts.append(structured["explanation"])
	return "\n\n".join(parts)


def generate_answer(state: GraphState, model: Optional[Any] = None) -> GraphState:
	"""Call Gemini (or an injected model) to produce a grounded, structured answer."""
	if not state.get("retrieved_documents"):
		message = (
			"I do not have enough retrieved constitutional material to answer this "
			"question reliably. Please try a more specific article, clause, or case name."
		)
		structured = {
			"summary": message,
			"sections": [],
			"key_clauses": [],
			"explanation": DISCLAIMER,
		}
		return {
			**state,
			"answer": f"Summary: {message}\n\n{DISCLAIMER}",
			"citations": [],
			**structured,
		}
	active_model = model or _get_model()
	prompt = build_prompt(state)
	raw: _RawStructuredAnswer = active_model.invoke(prompt)
	if isinstance(raw, dict):
		raw = _RawStructuredAnswer(**raw)

	lookup = _citation_lookup(state.get("retrieved_documents") or [])
	sections = [
		{
			"heading": section.heading,
			"body": section.body,
			"citations": _resolve_citations(section.cite_source_ids, lookup),
		}
		for section in raw.sections
	]
	summary_citations = _resolve_citations(raw.summary_cite_source_ids, lookup)
	key_clauses = [
		{
			"text": clause.text,
			"citations": _resolve_citations(clause.cite_source_ids, lookup),
		}
		for clause in raw.key_clauses
	]
	explanation = f"{raw.explanation}\n\n{DISCLAIMER}" if raw.explanation else DISCLAIMER

	structured = {
		"summary": raw.summary,
		"summary_citations": summary_citations,
		"sections": sections,
		"key_clauses": key_clauses,
		"explanation": explanation,
	}
	answer = _render_answer(structured)

	return {**state, "answer": answer, **structured}


def append_exchange(chat_history: list[Any], question: str, answer: str) -> None:
	"""Append a completed exchange to the conversation history."""
	chat_history.append(HumanMessage(content=question))
	chat_history.append(AIMessage(content=answer))

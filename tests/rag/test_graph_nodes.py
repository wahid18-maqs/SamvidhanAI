"""Unit tests for the Phase 3 LangGraph nodes."""

import unittest

from backend.graph.nodes.analyzer import analyze_query, classify_intent
from backend.graph.nodes.citations import build_citations, citation_for
from backend.graph.nodes.evaluation import evaluate_context, rewrite_query, route_after_evaluation
from backend.graph.nodes.generation import (
	LANGUAGE_NAMES,
	_RawKeyClause,
	_RawSection,
	_RawStructuredAnswer,
	build_prompt,
	generate_answer,
)
from backend.graph.nodes.metadata import build_metadata_filter
from backend.graph.nodes.retrieval import retrieve


class AnalyzerTests(unittest.TestCase):
	def test_article_reference_classified_as_article(self):
		state = analyze_query({"query": "What is Article 21?"})
		self.assertEqual(state["intent"], "article")
		self.assertEqual(state["metadata_filter"], {"article": {"$eq": "21"}})

	def test_article_368_classified_as_amendment(self):
		state = analyze_query({"query": "Explain Article 368 clause 2"})
		self.assertEqual(state["intent"], "amendment")

	def test_amendment_keyword_classified_as_amendment(self):
		self.assertEqual(classify_intent("How can the Constitution be amended?", {}), "amendment")

	def test_known_case_name_classified_as_case_law(self):
		self.assertEqual(classify_intent("Explain Kesavananda Bharati.", {}), "case_law")

	def test_registered_case_name_classified_as_case_law(self):
		self.assertEqual(
			classify_intent("What did the court hold in Maneka Gandhi v. Union of India?", {}),
			"case_law",
		)

	def test_history_keyword_classified_as_history(self):
		self.assertEqual(classify_intent("When was the Constitution adopted?", {}), "history")

	def test_unmatched_query_classified_as_general(self):
		self.assertEqual(classify_intent("Explain fundamental rights", {}), "general")

	def test_original_query_preserved_across_calls(self):
		state = analyze_query({"query": "rewritten query", "original_query": "first query"})
		self.assertEqual(state["original_query"], "first query")


class MetadataBuilderTests(unittest.TestCase):
	def test_article_intent_constrains_to_constitution(self):
		state = build_metadata_filter({"intent": "article", "metadata_filter": {"article": {"$eq": "21"}}})
		self.assertEqual(
			state["metadata_filter"],
			{"article": {"$eq": "21"}, "document_type": {"$eq": "constitution"}},
		)

	def test_case_law_intent_strips_article_and_clause(self):
		state = build_metadata_filter({
			"intent": "case_law",
			"metadata_filter": {"article": {"$eq": "21"}, "clause": {"$eq": "1"}},
		})
		self.assertEqual(state["metadata_filter"], {"document_type": {"$eq": "case_law"}})

	def test_general_intent_adds_no_document_type_constraint(self):
		state = build_metadata_filter({"intent": "general", "metadata_filter": {}})
		self.assertIsNone(state["metadata_filter"])

	def test_resolved_case_id_narrows_case_law_filter_to_that_case(self):
		state = build_metadata_filter({
			"intent": "case_law",
			"metadata_filter": {},
			"resolved_case_id": "golaknath_1967",
		})
		self.assertEqual(
			state["metadata_filter"],
			{
				"document_type": {"$eq": "case_law"},
				"case_id": {"$eq": "golaknath_1967"},
				"case_name": {"$eq": "I.C. Golaknath v. State of Punjab"},
			},
		)

	def test_no_resolved_case_id_leaves_case_law_filter_corpus_wide(self):
		state = build_metadata_filter({
			"intent": "case_law",
			"metadata_filter": {},
			"resolved_case_id": None,
		})
		self.assertEqual(state["metadata_filter"], {"document_type": {"$eq": "case_law"}})

	def test_resolved_case_id_ignored_outside_case_law_intent(self):
		# A stray resolved_case_id must never narrow a non-case-law search --
		# e.g. article intent should stay constitution-only regardless.
		state = build_metadata_filter({
			"intent": "article",
			"metadata_filter": {"article": {"$eq": "21"}},
			"resolved_case_id": "golaknath_1967",
		})
		self.assertNotIn("case_id", state["metadata_filter"])


class CaseIdResolutionTests(unittest.TestCase):
	"""Full analyze_query -> build_metadata_filter chain: a query naming one
	known case should narrow retrieval to that case's own vectors instead of
	searching the whole case-law corpus by embedding similarity alone (the
	gap that let Kesavananda Bharati crowd Golak Nath out of its own
	benchmark question's top 10 -- see ingestion.md)."""

	def _resolve(self, query: str) -> dict:
		state = build_metadata_filter(analyze_query({"query": query}))
		return state["metadata_filter"]

	def test_golaknath_query_narrows_to_golaknath(self):
		self.assertEqual(
			self._resolve("What did the Supreme Court decide in Golaknath v. State of Punjab?"),
			{
				"document_type": {"$eq": "case_law"},
				"case_id": {"$eq": "golaknath_1967"},
				"case_name": {"$eq": "I.C. Golaknath v. State of Punjab"},
			},
		)

	def test_kesavananda_bharati_query_narrows_to_kesavananda(self):
		self.assertEqual(
			self._resolve("What is the basic structure doctrine established in Kesavananda Bharati?"),
			{
				"document_type": {"$eq": "case_law"},
				"case_id": {"$eq": "kesavananda_bharati_1973"},
				"case_name": {"$eq": "Kesavananda Bharati v. State of Kerala"},
			},
		)

	def test_bommai_query_narrows_to_bommai(self):
		self.assertEqual(
			self._resolve("What did S.R. Bommai decide about Article 356 and President's Rule?"),
			{"document_type": {"$eq": "case_law"}, "case_id": {"$eq": "sr_bommai_1994"}},
		)

	def test_article_370_case_query_narrows_to_in_re_article_370(self):
		self.assertEqual(
			self._resolve("What did the Supreme Court hold in the Article 370 case?"),
			{"document_type": {"$eq": "case_law"}, "case_id": {"$eq": "in_re_article_370_2023"}},
		)

	def test_bare_article_370_reference_is_not_forced_to_the_case(self):
		# No case-law-flavored qualifier ("case"/"judgment"/"in re" ...) --
		# this should stay a plain constitution-article lookup, not get
		# rerouted to the case about that article.
		filter_ = self._resolve("What is the constitutional meaning of Article 370?")
		self.assertNotIn("case_id", filter_ or {})

	def test_generic_case_law_query_stays_corpus_wide(self):
		filter_ = self._resolve("What landmark case shaped the basic structure doctrine?")
		self.assertEqual(filter_, {"document_type": {"$eq": "case_law"}})

	def test_multi_case_query_does_not_force_a_single_case(self):
		filter_ = self._resolve(
			"Compare how Kesavananda Bharati and Golaknath treated Parliament's amending power."
		)
		self.assertEqual(filter_, {"document_type": {"$eq": "case_law"}})


class RetrievalNodeTests(unittest.TestCase):
	def test_document_type_filter_runs_a_single_search(self):
		class FakeRetriever:
			top_k = 10

			def retrieve(self, query, metadata_filter_override=None):
				self.calls = getattr(self, "calls", []) + [(query, metadata_filter_override)]
				return {
					"matches": [
						{"fields": {"text": "hit one", "article": "21", "document_type": "constitution"}},
						{"fields": {"text": "hit two"}},
					]
				}

		retriever = FakeRetriever()
		state = retrieve(
			{"query": "What is Article 21?", "metadata_filter": {"article": {"$eq": "21"}, "document_type": {"$eq": "constitution"}}},
			retriever=retriever,
		)
		self.assertEqual(len(retriever.calls), 1)
		self.assertEqual(
			retriever.calls[0],
			("What is Article 21?", {"article": {"$eq": "21"}, "document_type": {"$eq": "constitution"}}),
		)
		self.assertEqual(len(state["retrieved_documents"]), 2)
		# Each passage is tagged with its resolvable source_id so generation
		# can attribute a claim back to a specific citation.
		self.assertIn("[source_id: article_21]\nhit one", state["context"])
		self.assertIn("[source_id: unknown_source]\nhit two", state["context"])

	def test_no_document_type_filter_searches_both_corpora_and_combines(self):
		# The actual anti-crowding-out guarantee: a general/history-intent
		# query (no document_type in its filter) must not let a single
		# unconstrained search allow one corpus to squeeze the other out of
		# context entirely (see KNOWN_ISSUES.md's conceptual-query bug).
		class FakeRetriever:
			top_k = 4

			def retrieve(self, query, metadata_filter_override=None):
				self.calls = getattr(self, "calls", []) + [metadata_filter_override]
				if metadata_filter_override.get("document_type") == {"$eq": "constitution"}:
					return {"matches": [{"fields": {"text": "constitution hit", "article": "19", "document_type": "constitution"}}]}
				return {"matches": [
					{"fields": {"text": "case hit 1", "document_type": "case_law", "case_id": "x"}},
					{"fields": {"text": "case hit 2", "document_type": "case_law", "case_id": "x"}},
				]}

		retriever = FakeRetriever()
		state = retrieve({"query": "What freedom protects speech?", "metadata_filter": {}}, retriever=retriever)

		self.assertEqual(len(retriever.calls), 2)
		document_types_queried = {call["document_type"]["$eq"] for call in retriever.calls}
		self.assertEqual(document_types_queried, {"constitution", "case_law"})
		# Constitution text must actually be present in context, not
		# crowded out by however many case-law hits scored higher.
		self.assertIn("constitution hit", state["context"])
		self.assertIn("case hit", state["context"])
		# Constitutional text comes first (authoritative source before
		# interpretation, matching the generation system prompt's framing).
		self.assertLess(state["context"].index("constitution hit"), state["context"].index("case hit"))


class EvaluationTests(unittest.TestCase):
	def test_no_hits_is_weak(self):
		state = evaluate_context({"retrieved_documents": [], "context": ""})
		self.assertEqual(state["context_quality"], "weak")

	def test_low_score_hit_is_weak(self):
		state = evaluate_context({
			"retrieved_documents": [{"_score": 0.01, "fields": {"text": "x"}}],
			"context": "x",
		})
		self.assertEqual(state["context_quality"], "weak")

	def test_reasonable_score_hit_is_good(self):
		state = evaluate_context({
			"retrieved_documents": [{"_score": 0.25, "fields": {"text": "x"}}],
			"context": "x",
		})
		self.assertEqual(state["context_quality"], "good")

	def test_rewrite_clears_filter_and_increments_retry(self):
		state = rewrite_query({
			"query": "Article 999 rights",
			"original_query": "Article 999 rights",
			"metadata_filter": {"article": {"$eq": "999"}},
			"retry_count": 0,
		})
		self.assertIsNone(state["metadata_filter"])
		self.assertEqual(state["retry_count"], 1)

	def test_route_retries_once_then_forces_generation(self):
		weak_first_try = {"context_quality": "weak", "retry_count": 0}
		weak_second_try = {"context_quality": "weak", "retry_count": 1}
		good = {"context_quality": "good", "retry_count": 0}
		self.assertEqual(route_after_evaluation(weak_first_try), "rewrite")
		self.assertEqual(route_after_evaluation(weak_second_try), "generate")
		self.assertEqual(route_after_evaluation(good), "generate")


class GenerationPromptTests(unittest.TestCase):
	def test_prompt_requests_target_language(self):
		prompt = build_prompt({"query": "What is Article 21?", "language": "ta", "context": "context text", "chat_history": []})
		self.assertIn(LANGUAGE_NAMES["ta"], prompt)
		self.assertIn("context text", prompt)

	def test_prompt_defaults_to_english(self):
		prompt = build_prompt({"query": "q", "context": "", "chat_history": []})
		self.assertIn("English", prompt)

	def test_prompt_explains_labeled_source_id_citation_rule(self):
		prompt = build_prompt({"query": "q", "context": "", "chat_history": []})
		self.assertIn("source_id", prompt)


class CitationForTests(unittest.TestCase):
	def test_article_metadata_produces_article_citation(self):
		self.assertEqual(
			citation_for({"article": "21", "document_type": "constitution"}),
			{"source_id": "article_21", "label": "Article 21"},
		)

	def test_case_law_metadata_produces_case_citation(self):
		self.assertEqual(
			citation_for({
				"document_type": "case_law",
				"case_id": "maneka_gandhi_1978",
				"case_name": "Maneka Gandhi v. Union of India",
			}),
			{"source_id": "maneka_gandhi_1978", "label": "Maneka Gandhi v. Union of India"},
		)

	def test_unidentifiable_metadata_returns_none(self):
		self.assertIsNone(citation_for({}))


class BuildCitationsTests(unittest.TestCase):
	def test_flat_list_is_union_of_section_and_key_clause_citations(self):
		state = build_citations({
			"sections": [{"citations": [{"source_id": "article_21", "label": "Article 21"}]}],
			"key_clauses": [{"citations": [{"source_id": "article_14", "label": "Article 14"}]}],
		})
		self.assertEqual(
			state["citations"],
			[
				{"source_id": "article_21", "label": "Article 21"},
				{"source_id": "article_14", "label": "Article 14"},
			],
		)

	def test_duplicate_sources_across_pieces_are_deduplicated(self):
		citation = {"source_id": "article_21", "label": "Article 21"}
		state = build_citations({
			"sections": [{"citations": [citation]}],
			"key_clauses": [{"citations": [citation]}],
		})
		self.assertEqual(len(state["citations"]), 1)

	def test_no_sections_or_key_clauses_yields_empty_citations(self):
		state = build_citations({})
		self.assertEqual(state["citations"], [])


class GenerateAnswerResolutionTests(unittest.TestCase):
	"""The actual anti-fabrication guarantee: a source_id the model claims
	but that was never retrieved must be dropped, not passed through."""

	def test_unretrieved_source_id_is_dropped_retrieved_one_is_kept(self):
		class FakeStructuredModel:
			def invoke(self, prompt):
				return _RawStructuredAnswer(
					summary="Article 21 protects life and liberty.",
					sections=[
						_RawSection(
							heading="Article 21",
							body="No person shall be deprived of life or liberty except by procedure established by law.",
							cite_source_ids=["article_21", "article_999"],
						)
					],
					key_clauses=[
						_RawKeyClause(text="Procedure established by law", cite_source_ids=["article_999"])
					],
					explanation="This establishes a fundamental right.",
				)

		state = {
			"query": "What is Article 21?",
			"language": "en",
			"context": "[source_id: article_21]\n21. Protection of life...",
			"chat_history": [],
			"retrieved_documents": [
				{"fields": {"article": "21", "document_type": "constitution", "text": "21. Protection of life..."}}
			],
		}
		result = generate_answer(state, model=FakeStructuredModel())

		self.assertEqual(len(result["sections"]), 1)
		self.assertEqual(
			result["sections"][0]["citations"],
			[{"source_id": "article_21", "label": "Article 21"}],
		)
		# article_999 was never retrieved -- must not survive into either
		# the section or the key clause that claimed it.
		self.assertEqual(result["key_clauses"][0]["citations"], [])
		self.assertIn("This is a research aid, not legal advice.", result["explanation"])
		self.assertIn("Article 21", result["answer"])


if __name__ == "__main__":
	unittest.main()

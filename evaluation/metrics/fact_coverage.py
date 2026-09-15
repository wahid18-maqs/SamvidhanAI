"""Deterministic key-fact coverage: does the generated answer actually
mention the benchmark's expected_key_facts, with zero LLM judge calls?

This is the sklearn-based, API-budget-friendly replacement for DeepEval's
FaithfulnessMetric/HallucinationMetric (see evaluation/README.md). It's a
token-overlap proxy, not semantic entailment -- a paraphrase that keeps
the fact's substance but swaps most of its wording could be scored as
"not covered", and conversely a coincidental word overlap on an
unrelated sentence could be scored as "covered". That coarseness is the
deliberate trade for not spending any Gemini judge-call budget on it;
it catches the common case (the fact's substance, or a close paraphrase
of it, is just missing from the answer) without needing a model in the
loop.
"""

import re

from sklearn.metrics import recall_score

_STOPWORDS = {
	"the", "a", "an", "of", "to", "in", "on", "by", "and", "or", "for",
	"is", "are", "was", "were", "shall", "not", "any", "this", "that",
	"its", "be", "as", "with", "from", "at", "which", "who", "into",
	"under", "such", "may", "no", "person", "state",
}


def _content_words(text: str) -> set[str]:
	"""Lowercased alphanumeric tokens with short/common words dropped, so
	overlap is scored on the words actually carrying meaning."""
	words = re.findall(r"[a-z0-9]+", text.lower())
	return {word for word in words if word not in _STOPWORDS and len(word) > 2}


def fact_covered(fact: str, answer: str, threshold: float = 0.6) -> bool:
	"""True when at least `threshold` of the fact's content words also
	appear somewhere in the answer -- paraphrase-tolerant at the
	word level, but not a semantic check."""
	fact_words = _content_words(fact)
	if not fact_words:
		return False
	answer_words = _content_words(answer)
	return len(fact_words & answer_words) / len(fact_words) >= threshold


def fact_coverage_recall(covered_flags: list[bool]) -> float:
	"""Recall of expected facts actually covered, computed through
	sklearn.metrics for consistency with citation_relevance rather than
	a hand-rolled mean. Every fact in the benchmark is by definition
	expected (y_true is all 1s), so this reduces to the covered
	fraction -- sklearn.metrics.recall_score still applies cleanly here,
	it's just that this dataset never exercises its true-negative
	handling.
	"""
	if not covered_flags:
		return 0.0
	y_true = [1] * len(covered_flags)
	y_pred = [1 if flag else 0 for flag in covered_flags]
	return recall_score(y_true, y_pred, zero_division=0)

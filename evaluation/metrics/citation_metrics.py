"""Citation metrics for generation-quality eval -- no LLM judge calls.

Two distinct checks, both deterministic:

- `citation_validity`: the anti-fabrication guard. Does every source_id
  the pipeline actually cited appear in what was actually retrieved?
  backend/graph/nodes/generation.py's `_resolve_citations` already drops
  any model-claimed source_id that isn't in the retrieved set, so this
  is a runtime regression guard on that guarantee, not expected to ever
  fail against the current pipeline. Plain set containment -- no
  sklearn needed for a single question, but see `citation_relevance`
  below for the batch-level metric that does use it.

- `citation_relevance`: does what actually got cited match the
  benchmark's expected_source_ids? This is a real multi-label
  classification problem (a question can expect/cite more than one
  source), so it's computed with sklearn.metrics'
  precision_score/recall_score/f1_score over a
  sklearn.preprocessing.MultiLabelBinarizer-encoded label matrix,
  "samples"-averaged across all questions in the run.

Previously this lived in a DeepEval `BaseMetric` subclass backed by a
Gemini judge model (see git history) -- moved off DeepEval entirely
because the judge-model calls (several per metric per question, on top
of the pipeline's own generation call) couldn't be sustained on this
project's free-tier Gemini quota. Both checks here need zero extra LLM
calls.
"""

from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.preprocessing import MultiLabelBinarizer


def citation_validity(cited_source_ids: list[str], available_source_ids: set[str]) -> float:
	"""Fraction of cited_source_ids that were actually retrieved.

	1.0 when nothing was cited (nothing to be wrong about) or every
	citation is grounded in what was retrieved; lower means the model
	claimed a source it never actually saw -- a fabricated citation.
	"""
	cited = set(cited_source_ids)
	if not cited:
		return 1.0
	return len(cited & available_source_ids) / len(cited)


def citation_relevance(
	expected_source_ids: list[list[str]], cited_source_ids: list[list[str]]
) -> dict:
	"""Multi-label precision/recall/F1 of cited vs. expected source_ids,
	"samples"-averaged (per question, then meaned) across a whole eval
	run. `expected_source_ids[i]`/`cited_source_ids[i]` are the two label
	sets for question i; the lists must be the same length.
	"""
	if len(expected_source_ids) != len(cited_source_ids):
		raise ValueError("expected_source_ids and cited_source_ids must be the same length")

	# sklearn's "samples" average requires a genuinely multilabel-shaped
	# indicator matrix (2+ label columns) -- with as few as one distinct
	# source_id across the whole run (e.g. a single-question --limit 1
	# smoke test), MultiLabelBinarizer only produces one column and
	# sklearn refuses samples-averaging on it ("not available outside of
	# multilabel classification"). Two inert placeholder labels that
	# never appear in any real question guarantee at least 2 columns
	# without affecting the real precision/recall math: both columns are
	# 0 in every row of both y_true and y_pred, so they contribute
	# neither a true positive, false positive, nor false negative to any
	# sample's score.
	placeholders = [["__pad_a__"], ["__pad_b__"]]
	mlb = MultiLabelBinarizer()
	mlb.fit(expected_source_ids + cited_source_ids + placeholders)
	y_true = mlb.transform(expected_source_ids)
	y_pred = mlb.transform(cited_source_ids)

	return {
		"precision": precision_score(y_true, y_pred, average="samples", zero_division=0),
		"recall": recall_score(y_true, y_pred, average="samples", zero_division=0),
		"f1": f1_score(y_true, y_pred, average="samples", zero_division=0),
	}

"""Generation-quality eval: runs each question through the real chat
pipeline (backend.graph.workflow.run -- same function /api/chat calls)
and scores the actual answer with deterministic, LLM-judge-free metrics
from sklearn.metrics.

Previously used DeepEval's FaithfulnessMetric/HallucinationMetric with a
Gemini judge model. Moved off that: each of those metrics makes several
judge-model calls per question on top of the generation call itself, and
this project's free-tier Gemini quota (5 req/min) can't sustain that
multiplier. Now scores two deterministic checks instead, both needing
zero extra LLM calls:

- citation_relevance / citation_validity (evaluation/metrics/
  citation_metrics.py): does the answer cite the sources the benchmark
  expects, and never a source it wasn't actually given?
- fact_coverage (evaluation/metrics/fact_coverage.py): does the answer's
  text actually mention the benchmark's expected key facts (a token-
  overlap proxy, not semantic entailment -- coarser than an LLM judge,
  see that module's docstring for the trade-off).

Still live by design -- every question makes one real Gemini generation
call and one real Pinecone retrieval call through the actual graph. Just
no judge-model calls layered on top of that.

Field mapping: state["query"] -> input, state["answer"] -> actual_output,
state["retrieved_documents"] (returned here as result["context"]) ->
what "available" sources were actually retrieved.
"""

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.graph.nodes.citations import citation_for  # noqa: E402
from backend.graph.workflow import run as run_chat_graph  # noqa: E402
from evaluation.metrics.citation_metrics import citation_relevance, citation_validity  # noqa: E402
from evaluation.metrics.fact_coverage import fact_covered, fact_coverage_recall  # noqa: E402

QUESTIONS_PATH = PROJECT_ROOT / "evaluation" / "datasets" / "generation_questions.json"

# Gemini free tier is 5 req/min. This runner makes exactly one real
# Gemini call per question now (the generation call itself -- no
# judge-model calls stacked on top), so a smaller pace than the old
# DeepEval-era 20s still leaves comfortable margin against 429s.
PACING_SECONDS = 13


def load_questions() -> list[dict]:
	return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


def retrieved_source_ids(retrieved_documents: list[dict]) -> set[str]:
	ids = set()
	for hit in retrieved_documents or []:
		citation = citation_for(hit.get("fields", {}))
		if citation:
			ids.add(citation["source_id"])
	return ids


def run_one(item: dict) -> dict:
	result = run_chat_graph(item["question"], language="en")
	available_ids = retrieved_source_ids(result["context"])
	cited_ids = [c["source_id"] for c in result["citations"]]
	covered_flags = [fact_covered(fact, result["answer"]) for fact in item["expected_key_facts"]]

	return {
		"id": item["id"],
		"category": item["category"],
		"question": item["question"],
		"answer": result["answer"],
		"cited_source_ids": cited_ids,
		"expected_source_ids": item["expected_source_ids"],
		"citation_validity_score": citation_validity(cited_ids, available_ids),
		"covered_flags": covered_flags,
		"fact_coverage_score": fact_coverage_recall(covered_flags),
	}


def _print_group(label: str, records: list[dict]) -> None:
	if not records:
		return
	relevance = citation_relevance(
		[r["expected_source_ids"] for r in records],
		[r["cited_source_ids"] for r in records],
	)
	mean_validity = sum(r["citation_validity_score"] for r in records) / len(records)
	overall_fact_coverage = fact_coverage_recall(
		[flag for r in records for flag in r["covered_flags"]]
	)
	print(f"\n{label} questions: {len(records)}")
	print(
		f"{label} Citation Relevance vs. expected sources -- "
		f"Precision: {relevance['precision']:.2%} "
		f"Recall: {relevance['recall']:.2%} "
		f"F1: {relevance['f1']:.2%}"
	)
	print(f"{label} Mean Citation Validity (no fabricated citations): {mean_validity:.2%}")
	print(f"{label} Fact Coverage Recall: {overall_fact_coverage:.2%}")


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--limit", type=int, default=None, help="only run the first N questions")
	args = parser.parse_args()

	questions = load_questions()
	if args.limit:
		questions = questions[: args.limit]

	results = []
	for index, item in enumerate(questions):
		if index > 0:
			time.sleep(PACING_SECONDS)
		print(f"Running {item['id']} ({item['category']}): {item['question']}")
		record = run_one(item)
		results.append(record)
		print(
			f"  citation_validity={record['citation_validity_score']:.2f} "
			f"fact_coverage={record['fact_coverage_score']:.2f}"
		)

	_print_group("All", results)
	by_category = defaultdict(list)
	for record in results:
		by_category[record["category"]].append(record)
	for category, records in by_category.items():
		_print_group(category, records)


if __name__ == "__main__":
	main()

# Evaluation

Benchmark datasets, metrics, and runners for measuring ConstituteAI's
retrieval and generation quality.

## Current structure

```
evaluation/
├── datasets/
│   ├── retrieval_questions.json    # question -> expected source_ids + category
│   └── generation_questions.json   # question -> expected source_ids + expected_key_facts + category
├── metrics/
│   ├── citation_metrics.py         # citation_validity + citation_relevance (sklearn.metrics)
│   └── fact_coverage.py            # fact_covered + fact_coverage_recall (sklearn.metrics)
├── runners/
│   ├── run_retrieval_eval.py       # runs questions through the real LangGraph
│   │                                # retrieval path, reports Recall@K/Precision@K
│   └── run_generation_eval.py      # runs questions through the real chat pipeline,
│                                    # scores citation + fact-coverage metrics
├── results/                        # empty for now (see below)
└── README.md
```

`results/` is a placeholder — see "Planned, not yet built" below. Nothing
currently writes into it; both runners print to stdout only.

## Why sklearn.metrics, not an LLM judge

Generation eval used to run each answer through DeepEval's
`FaithfulnessMetric`/`HallucinationMetric` with a Gemini judge model.
Moved off that: each of those metrics makes several extra judge-model
calls per question, on top of the pipeline's own generation call, and
this project's free-tier Gemini quota (5 req/min) can't sustain that
multiplier for a whole benchmark run.

`run_generation_eval.py` now scores two deterministic checks instead,
both computed with `sklearn.metrics` and needing zero extra LLM calls
beyond the one real generation call each question already makes:

- **citation_relevance** / **citation_validity**
  (`evaluation/metrics/citation_metrics.py`) — does the answer cite the
  sources the benchmark expects (multi-label precision/recall/F1 via
  `sklearn.metrics` + `MultiLabelBinarizer`), and does it never cite a
  source it wasn't actually given (plain set containment — the
  anti-fabrication guard)?
- **fact_coverage** (`evaluation/metrics/fact_coverage.py`) — does the
  answer's text actually mention the benchmark's `expected_key_facts`?
  A token-overlap proxy scored via `sklearn.metrics.recall_score`, not
  semantic entailment — coarser than an LLM judge (a heavy paraphrase
  can under-score, a coincidental word overlap can over-score), but the
  deliberate trade for spending zero judge-call budget on it.

This trades semantic judgment for something checkable and free. It will
not catch a fluent-sounding but subtly wrong answer that happens to
reuse the right words — if that gap matters more than the API budget
constraint, an LLM-judge metric (DeepEval, Ragas, or a bespoke Gemini
judge) is the more sensitive tool; this setup is the one that survives a
constrained quota.

## Running the retrieval eval

```bash
# Local metadata fixture (no live Pinecone call, fast, deterministic)
PYTHONPATH=. python evaluation/runners/run_retrieval_eval.py

# Against the real configured Pinecone index
PYTHONPATH=. python evaluation/runners/run_retrieval_eval.py --live

# Options
--top-k N        # default 10
--namespace NAME # default from backend.config.PINECONE_NAMESPACE
--no-rerank      # disable hosted reranking even if RERANK_ENABLED=true
```

The runner chains the same LangGraph nodes `/api/chat` actually uses
(`analyze_query` -> `build_metadata_filter` -> `retrieve`), not the raw
retriever directly — a fix to intent routing or the dual-corpus retrieval
logic in `backend/graph/nodes/retrieval.py` shows up here immediately,
rather than the benchmark silently drifting from what a live request does.

## What the metrics mean

- **Recall@K** — of the source_ids a question expects, what fraction did
  retrieval actually surface in its top K results? Misses mean the
  right answer was never even available to the generation step.
- **Precision@K** — of what retrieval surfaced, what fraction was
  actually relevant (in the expected set)? Low precision means correct
  answers are getting diluted by irrelevant retrieved context.
- Results are also broken down per question `category`
  (`explicit-article`, `conceptual`, `case-law`) — a conceptual-query
  weakness (see `KNOWN_ISSUES.md`) doesn't get masked by strong
  explicit-article numbers when averaged together.

## `evaluation/datasets/retrieval_questions.json` format

```json
{
  "id": "q01",
  "question": "What is Article 1 of the Constitution of India?",
  "expected_source_ids": ["article_1"],
  "category": "explicit-article"
}
```

`category` is one of `explicit-article`, `conceptual`, `case-law`.
`expected_source_ids` is the full set of source_ids retrieval should
surface for this question — an article number (`article_21`) or a case
slug (`maneka_gandhi_1978`), matching `backend/graph/nodes/citations.py`'s
`citation_for()` source_id convention.

## Running the generation eval

```bash
PYTHONPATH=. python evaluation/runners/run_generation_eval.py

# only the first N questions, e.g. while iterating
PYTHONPATH=. python evaluation/runners/run_generation_eval.py --limit 3
```

Fully live: every question makes one real Gemini generation call and one
real Pinecone retrieval call through the actual `backend.graph.workflow.run`
(the same function `/api/chat` calls). Paced 13s apart to stay under
free-tier Gemini's 5 req/min — a full 12-question run takes a couple of
minutes minimum. See "Why sklearn.metrics, not an LLM judge" above for
what's actually scored and why.

## `evaluation/datasets/generation_questions.json` format

```json
{
  "id": "g01",
  "question": "What does Article 14 guarantee?",
  "expected_source_ids": ["article_14"],
  "expected_key_facts": [
    "The State shall not deny to any person equality before the law",
    "The State shall not deny to any person the equal protection of the laws",
    "This protection applies within the territory of India"
  ],
  "golden_answer": null,
  "category": "explicit-article"
}
```

`expected_key_facts` feeds `fact_coverage`; `golden_answer` is reserved
for a future exact/semantic-similarity comparison and is `null` on every
question today — nothing currently reads it.

## Planned, not yet built

- **Results persistence** — `evaluation/results/` will hold timestamped,
  versioned run outputs (e.g. `2026-08-31_v3_baseline.json` + a
  human-readable `.md` summary) once a runner actually writes results to
  disk instead of just stdout. Both runners print to stdout only today.
- **`run_e2e_eval.py`** — a runner scoring the full query -> graph ->
  answer path against both retrieval and generation metrics in one pass,
  rather than the two separate runners today.
- **`evaluation/metrics/retrieval_metrics.py`** — worth extracting the
  Recall/Precision math out of `run_retrieval_eval.py` into its own
  reusable module if a third caller ever needs it.
- **Golden-answer comparison** — `generation_questions.json`'s
  `golden_answer` field is reserved for this but unused; every question
  has it set to `null` today.

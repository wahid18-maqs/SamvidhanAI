"""Metadata-aware semantic retrieval for ConstituteAI."""

import re
import time
from typing import Any, Dict, Optional

from backend.config import PINECONE_NAMESPACE, RERANK_ENABLED
from backend.rag.reranker import PineconeReranker
from backend.services.pinecone import PineconeService


ARTICLE_PATTERN = re.compile(
	r"\b(?:article|art\.?)[\s.-]*(\d{1,3}[A-Z]?)\b", re.IGNORECASE
)
CLAUSE_PATTERN = re.compile(r"\bclause\s*\(?\s*([0-9]+|[a-z])\s*\)?", re.IGNORECASE)
TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)?", re.IGNORECASE)
LEXICAL_STOPWORDS = {
	"a", "an", "and", "are", "be", "by", "for", "from", "in", "is",
	"of", "on", "or", "that", "the", "to", "what", "when", "which",
	"who", "with",
}


def is_embedding_quota_error(error: Exception) -> bool:
	"""Identify Pinecone's non-transient monthly embedding quota response."""
	return "embedding token limit" in str(error).lower() and "resource_exhausted" in str(error).lower()


def extract_metadata_filter(query: str) -> Dict[str, Dict[str, str]]:
	"""Extract article and clause references present in indexed metadata."""
	metadata_filter: Dict[str, Dict[str, str]] = {}
	article_match = ARTICLE_PATTERN.search(query)
	if article_match:
		metadata_filter["article"] = {"$eq": article_match.group(1).upper()}
	clause_match = CLAUSE_PATTERN.search(query)
	if clause_match:
		metadata_filter["clause"] = {"$eq": clause_match.group(1).lower()}
	return metadata_filter


def _query_terms(query: str) -> set[str]:
	return {
		token.lower()
		for token in TOKEN_PATTERN.findall(query)
		if token.lower() not in LEXICAL_STOPWORDS and len(token) > 1
	}


def _bm25_scores(query: str, documents: list[str]) -> list[float]:
	"""Score candidate passages with a small dependency-free BM25 ranker."""
	query_terms = _query_terms(query)
	tokenized = [
		[token.lower() for token in TOKEN_PATTERN.findall(document)]
		for document in documents
	]
	if not query_terms or not tokenized:
		return [0.0] * len(documents)
	average_length = sum(len(document) for document in tokenized) / len(tokenized) or 1
	document_frequency = {
		term: sum(term in set(document) for document in tokenized)
		for term in query_terms
	}
	k1 = 1.2
	b = 0.75
	scores = []
	for document in tokenized:
		frequencies = {term: document.count(term) for term in query_terms}
		score = 0.0
		for term, frequency in frequencies.items():
			if not frequency:
				continue
			idf = ((len(tokenized) - document_frequency[term] + 0.5) /
				(document_frequency[term] + 0.5))
			idf = max(0.0, idf)
			numerator = frequency * (k1 + 1)
			denominator = frequency + k1 * (1 - b + b * len(document) / average_length)
			score += idf * numerator / denominator
		scores.append(score)
	return scores


def _hybrid_rank_hits(query: str, hits: list[dict], top_k: int) -> list[dict]:
	"""Blend Pinecone similarity with BM25 term relevance for legal phrases."""
	terms = _query_terms(query)
	if not terms or len(hits) < 2:
		return hits[:top_k]

	semantic_scores = [float(hit.get("_score", hit.get("score", 0)) or 0) for hit in hits]
	bm25_scores = _bm25_scores(
		query, [str(hit.get("fields", {}).get("text", "")) for hit in hits]
	)
	maximum_bm25 = max(bm25_scores) if bm25_scores else 0.0
	minimum = min(semantic_scores)
	maximum = max(semantic_scores)
	score_range = maximum - minimum
	for index, (hit, semantic_score) in enumerate(zip(hits, semantic_scores)):
		fields = hit.get("fields", {})
		text = str(fields.get("text", ""))
		bm25 = bm25_scores[index]
		normalized_bm25 = bm25 / maximum_bm25 if maximum_bm25 else 0.0
		phrase_bonus = 0.15 if query.lower().strip() in text.lower() else 0.0
		normalized_semantic = (
			(semantic_score - minimum) / score_range if score_range else 1.0
		)
		hit["_hybrid_score"] = 0.35 * normalized_semantic + 0.65 * normalized_bm25 + phrase_bonus
	return sorted(hits, key=lambda hit: hit.get("_hybrid_score", 0), reverse=True)[:top_k]


def _apply_hybrid_rank(response: Any, query: str, top_k: int) -> Any:
	"""Apply local lexical reranking while preserving Pinecone response shape."""
	if not isinstance(response, dict):
		return response
	if "matches" in response:
		response["matches"] = _hybrid_rank_hits(query, response["matches"], top_k)
		return response
	result = response.get("result")
	if isinstance(result, dict) and "hits" in result:
		result["hits"] = _hybrid_rank_hits(query, result["hits"], top_k)
	return response


class PineconeRetriever:
	"""Run metadata-filtered semantic retrieval with Pinecone embeddings."""

	def __init__(
		self,
		pinecone_service: PineconeService,
		top_k: int = 10,
		namespace: str = PINECONE_NAMESPACE,
		candidate_k: int = 25,
		reranker: Optional[PineconeReranker] = None,
		use_reranker: bool = RERANK_ENABLED,
	):
		if top_k <= 0:
			raise ValueError("top_k must be positive")
		if candidate_k < top_k:
			raise ValueError("candidate_k must be at least top_k")
		self.pinecone_service = pinecone_service
		self.top_k = top_k
		self.namespace = namespace
		self.reranker = reranker or (
			PineconeReranker(pinecone_service, candidate_k, top_k)
			if use_reranker
			else None
		)
		self.last_retrieval_latency_ms = 0.0
		self.last_rerank_latency_ms = 0.0

	def retrieve(self, query: str, metadata_filter_override: Optional[dict] = None) -> Any:
		"""Return semantic matches constrained by explicit or derived metadata.

		`metadata_filter_override` lets a caller (e.g. the LangGraph retrieval
		node, which has already combined intent-based and regex-derived
		filters) supply the filter directly instead of having it re-derived
		from the raw query text. `None` preserves the original behavior of
		deriving the filter here via `extract_metadata_filter`. Pass `{}`
		explicitly to force an unfiltered search.
		"""
		if not query.strip():
			raise ValueError("query must not be empty")
		if metadata_filter_override is not None:
			metadata_filter = metadata_filter_override or None
		else:
			metadata_filter = extract_metadata_filter(query) or None
		started = time.perf_counter()
		try:
			if self.reranker:
				response = self.reranker.retrieve(
					query, metadata_filter, self.namespace
				)
				self.last_rerank_latency_ms = self.reranker.last_latency_ms
			else:
				response = self.pinecone_service.search_text(
					text=query,
					top_k=self.top_k,
					filter=metadata_filter,
					namespace=self.namespace,
				)
				self.last_rerank_latency_ms = 0.0
		except Exception as error:
			if not is_embedding_quota_error(error):
				raise
			response = {"matches": []}
			self.last_rerank_latency_ms = 0.0
		response = _apply_hybrid_rank(response, query, self.top_k)
		self.last_retrieval_latency_ms = (time.perf_counter() - started) * 1000
		return response


def create_retriever(
	top_k: int = 10,
	namespace: str = PINECONE_NAMESPACE,
	use_reranker: bool = RERANK_ENABLED,
) -> PineconeRetriever:
	"""Build the configured Pinecone integrated-embedding retriever."""
	return PineconeRetriever(
		pinecone_service=PineconeService(),
		top_k=top_k,
		namespace=namespace,
		use_reranker=use_reranker,
	)

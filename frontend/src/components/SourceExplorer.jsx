import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight, X } from "lucide-react";
import { getSource } from "../services/api";

/** Section 1.5/1.6: opens on citation click, closable, scrolls
 * independently. Extended per Ui updates and features.md 2.1's
 * content-shapes table to render three different content shapes off one
 * generic `request.load()` result — the panel itself doesn't know which
 * caller asked for which:
 *  - { title, sources }  — one or several full source blocks (citation
 *    click, Search by Number, Fundamental Rights/DPSP sub-items, Case
 *    Studies -> Landmark Judgments)
 *  - { title, results }  — a ranked/literal snippet list (Search by
 *    Topic, Full-Text Search), each row expandable in place via getSource
 *  - { title, analyses }  — static case-significance summaries (Case
 *    Analysis), plain text blocks, nothing to expand
 */
export default function SourceExplorer({ request, onClose }) {
  const [title, setTitle] = useState(request.title || "Source Explorer");
  const [sources, setSources] = useState(null);
  const [results, setResults] = useState(null);
  const [analyses, setAnalyses] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setSources(null);
    setResults(null);
    setAnalyses(null);
    setError(null);
    setLoading(true);
    setTitle(request.title || "Source Explorer");
    request
      .load()
      .then((result) => {
        if (!active) return;
        setTitle(result.title || "Source Explorer");
        setSources(result.sources || null);
        setResults(result.results || null);
        setAnalyses(result.analyses || null);
      })
      .catch((err) => active && setError(err.message || "Could not load this source."))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [request]);

  const items = sources ?? results ?? analyses;

  return (
    <aside className="fixed inset-0 z-50 flex flex-col bg-panel shadow-2xl lg:static lg:inset-auto lg:z-auto lg:h-screen lg:w-96 lg:shrink-0 lg:border-l lg:border-border">
      <div className="flex h-16 items-center justify-between border-b border-border px-5">
        <h2 className="truncate text-sm font-semibold text-heading">{title}</h2>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="shrink-0 text-muted hover:text-heading"
        >
          <X size={18} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-5 text-sm">
        {loading && <p className="text-muted">Loading…</p>}
        {error && <p className="text-red-400">{error}</p>}
        {!loading && !error && items?.length === 0 && (
          <p className="text-muted">Nothing found for this selection.</p>
        )}
        {sources?.length > 0 && (
          <div className="space-y-6">
            {sources.map((source) => (
              <SourceBlock key={source.source_id} source={source} />
            ))}
          </div>
        )}
        {results?.length > 0 && (
          <div className="space-y-2">
            {results.map((result) => (
              <ResultRow key={result.source_id} result={result} />
            ))}
          </div>
        )}
        {analyses?.length > 0 && (
          <div className="space-y-5">
            {analyses.map((item) => (
              <div key={item.case_id}>
                <p className="text-xs font-medium uppercase tracking-wide text-gold">
                  {item.case_name}
                  {item.year ? ` (${item.year})` : ""}
                </p>
                <p className="mt-1.5 whitespace-pre-wrap text-body">{item.analysis}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}

function SourceBlock({ source }) {
  return (
    <div>
      <div className="rounded-xl border border-border bg-base/60 p-4">
        <p className="text-xs font-medium uppercase tracking-wide text-muted">
          {source.document}
          {source.article ? ` · Art. ${source.article}` : ""}
          {source.page ? ` · p.${source.page}` : ""}
        </p>
        <p className="mt-2 whitespace-pre-wrap text-body">{source.original_text}</p>
      </div>

      {source.related_cases.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-medium uppercase tracking-wide text-muted">
            Landmark Supreme Court judgments
          </p>
          <ul className="mt-2 space-y-2">
            {source.related_cases.map((item) => (
              <li key={item} className="rounded-lg border border-border p-2 text-body">
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/** One Search by Topic result: label + score + snippet, expandable in
 * place to the full source (fetched on first expand, then cached). */
function ResultRow({ result }) {
  const [expanded, setExpanded] = useState(false);
  const [source, setSource] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function toggle() {
    const next = !expanded;
    setExpanded(next);
    if (next && !source && !loading) {
      setLoading(true);
      setError(null);
      getSource(result.source_id)
        .then(setSource)
        .catch((err) => setError(err.message || "Could not load this source."))
        .finally(() => setLoading(false));
    }
  }

  return (
    <div className="rounded-xl border border-border bg-base/60">
      <button
        type="button"
        onClick={toggle}
        className="flex w-full items-start gap-2 p-3 text-left"
      >
        {expanded ? (
          <ChevronDown size={14} className="mt-0.5 shrink-0 text-muted" />
        ) : (
          <ChevronRight size={14} className="mt-0.5 shrink-0 text-muted" />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs font-medium uppercase tracking-wide text-gold">{result.label}</p>
            {result.score != null && (
              <span className="shrink-0 text-xs text-muted">{result.score.toFixed(2)}</span>
            )}
          </div>
          {!expanded && (
            <p className="mt-1 line-clamp-3 whitespace-pre-wrap text-body-muted">{result.snippet}</p>
          )}
        </div>
      </button>
      {expanded && (
        <div className="px-3 pb-3">
          {loading && <p className="text-muted">Loading…</p>}
          {error && <p className="text-red-400">{error}</p>}
          {source && <p className="whitespace-pre-wrap text-body">{source.original_text}</p>}
        </div>
      )}
    </div>
  );
}

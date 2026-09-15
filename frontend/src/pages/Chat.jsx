import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import MessageBubble from "../components/MessageBubble";
import SourceExplorer from "../components/SourceExplorer";
import {
  getArticleGroup,
  getCaseAnalyses,
  getCases,
  getHistory,
  getSource,
  postChat,
  postShare,
  search,
  searchFulltext,
} from "../services/api";

/**
 * Chat interface wired to the real Pinecone-backed /api/chat endpoint.
 * The top-bar search box, quick-action chips, and sidebar topic nav all
 * feed into the same chat pipeline — there's no separate search results
 * view or /api/search endpoint yet, so "search" here means "ask the
 * assistant," which the backend already answers well for this kind of
 * query. The language selector is still a separate, later step.
 */
export default function Chat() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchValue, setSearchValue] = useState("");
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [conversationId, setConversationId] = useState(
    () => searchParams.get("conversation") || crypto.randomUUID(),
  );
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [explorerRequest, setExplorerRequest] = useState(null);
  const [language, setLanguage] = useState("en");
  const [shareStatus, setShareStatus] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const searchInputRef = useRef(null);

  // Loading an existing conversation from History (?conversation=<id>).
  // Structured messages (summary/sections/key_clauses/explanation) are
  // persisted alongside the flat content, so a loaded conversation renders
  // identically to how it looked live, not degraded to flat text.
  useEffect(() => {
    const existingId = searchParams.get("conversation");
    if (!existingId) return;
    setConversationId(existingId);
    getHistory(existingId)
      .then((data) => {
        setMessages(
          data.messages.map((message) => ({
            id: message.id,
            role: message.role,
            content: message.content,
            summary: message.summary,
            sections: message.sections,
            keyClauses: message.key_clauses,
            explanation: message.explanation,
          })),
        );
      })
      .catch((err) => setError(err.message || "Could not load this conversation."));
  }, [searchParams]);

  function handleNewChat() {
    setMessages([]);
    setDraft("");
    setSearchValue("");
    setError(null);
    setExplorerRequest(null);
    setConversationId(crypto.randomUUID());
    setSearchParams({});
    setSidebarOpen(false);
  }

  async function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed || sending) return;

    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content: trimmed }]);
    setError(null);
    setSending(true);
    try {
      const response = await postChat(trimmed, language, conversationId);
      setMessages((prev) => [
        ...prev,
        {
          id: response.message_id,
          role: "assistant",
          content: response.answer,
          citations: response.citations,
          summary: response.summary,
          sections: response.sections,
          keyClauses: response.key_clauses,
          explanation: response.explanation,
        },
      ]);
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setSending(false);
    }
  }

  function handleDraftSubmit(event) {
    event.preventDefault();
    sendMessage(draft);
    setDraft("");
  }

  function handleSearchSubmit(event) {
    event.preventDefault();
    if (!searchValue.trim()) return;
    sendMessage(searchValue);
    setSearchValue("");
  }

  function handleQuickAction(label) {
    setSearchValue("");
    sendMessage(label);
  }

  // Sidebar sub-item handlers (Ui updates and features.md 2.2 A1/B2) — each
  // opens the Source Explorer against a different backend shape, but the
  // panel itself only ever sees a { title, sources } loader (see
  // SourceExplorer.jsx), so none of this needs a new panel component.
  function handleCategorySelect(categoryKey, label) {
    setExplorerRequest({
      title: label,
      load: () => getArticleGroup(categoryKey).then((data) => ({ title: data.label, sources: data.sources })),
    });
    setSidebarOpen(false);
  }

  function handleCasesSelect() {
    setExplorerRequest({
      title: "Landmark Judgments",
      load: () => getCases().then((data) => ({ title: data.label, sources: data.sources })),
    });
    setSidebarOpen(false);
  }

  function handleArticleNumber(number) {
    const label = `Article ${number}`;
    setExplorerRequest({
      title: label,
      load: () => getSource(`article_${number}`).then((source) => ({ title: label, sources: [source] })),
    });
    setSidebarOpen(false);
  }

  function handleTopicSearch(query) {
    setExplorerRequest({
      title: `Search: ${query}`,
      load: () => search(query).then((data) => ({ title: `Search: ${data.query}`, results: data.results })),
    });
    setSidebarOpen(false);
  }

  function handleFulltextSearch(query) {
    setExplorerRequest({
      title: `Full-Text: ${query}`,
      load: () =>
        searchFulltext(query).then((data) => ({ title: `Full-Text: ${data.query}`, results: data.results })),
    });
    setSidebarOpen(false);
  }

  function handleCaseAnalysis() {
    setExplorerRequest({
      title: "Case Analysis",
      load: () => getCaseAnalyses().then((data) => ({ title: data.label, analyses: data.analyses })),
    });
    setSidebarOpen(false);
  }

  function handleCitationClick(citation) {
    setExplorerRequest({
      title: citation.label,
      load: () => getSource(citation.source_id).then((source) => ({ title: citation.label, sources: [source] })),
    });
  }

  async function handleShare() {
    if (messages.length === 0) return;
    setShareStatus("Sharing…");
    try {
      const { share_id } = await postShare(conversationId);
      const link = `${window.location.origin}/share/${share_id}`;
      await navigator.clipboard.writeText(link);
      setShareStatus("Link copied!");
    } catch (err) {
      setShareStatus(err.message || "Could not create a share link.");
    } finally {
      setTimeout(() => setShareStatus(null), 4000);
    }
  }

  return (
    <div className="flex h-screen bg-base">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewChat={handleNewChat}
        onCategorySelect={handleCategorySelect}
        onCasesSelect={handleCasesSelect}
        onArticleNumber={handleArticleNumber}
        onTopicSearch={handleTopicSearch}
        onFulltextSearch={handleFulltextSearch}
        onCaseAnalysis={handleCaseAnalysis}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          onMenuClick={() => setSidebarOpen(true)}
          searchValue={searchValue}
          onSearchChange={setSearchValue}
          onSearchSubmit={handleSearchSubmit}
          onQuickAction={handleQuickAction}
          searchInputRef={searchInputRef}
          language={language}
          onLanguageChange={setLanguage}
          onShare={handleShare}
          shareStatus={shareStatus}
        />

        <main className="flex-1 space-y-6 overflow-y-auto p-4 sm:p-6">
          {messages.length === 0 ? (
            <p className="text-sm text-muted">
              Ask a question about the Constitution to get started.
            </p>
          ) : (
            messages.map((message) => (
              <MessageBubble key={message.id} {...message} onCitationClick={handleCitationClick} />
            ))
          )}
          {sending && <p className="text-sm text-muted">Thinking…</p>}
          {error && <p className="text-sm text-red-400">{error}</p>}
        </main>

        <form onSubmit={handleDraftSubmit} className="flex gap-2 border-t border-border bg-base px-4 py-4 sm:px-6">
          <input
            type="text"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Type your question…"
            disabled={sending}
            className="min-w-0 flex-1 rounded-xl border border-border bg-panel px-4 py-2 text-sm text-heading placeholder-muted focus:border-gold focus:outline-none disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={sending}
            className="shrink-0 rounded-xl bg-gold-gradient px-5 py-2 text-sm font-medium text-base transition hover:opacity-95 disabled:opacity-60"
          >
            Send
          </button>
        </form>
      </div>

      {explorerRequest && (
        <SourceExplorer request={explorerRequest} onClose={() => setExplorerRequest(null)} />
      )}
    </div>
  );
}

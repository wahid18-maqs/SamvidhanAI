import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import MessageBubble from "../components/MessageBubble";
import SourceExplorer from "../components/SourceExplorer";
import ChatComposer from "../components/ChatComposer";
import {
  getArticleGroup,
  getCaseAnalyses,
  getCases,
  getHistory,
  getSource,
  postChat,
  postShare,
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
  const [conversationRefreshKey, setConversationRefreshKey] = useState(0);
  const refreshedNewConversation = useRef(false);
  const messagesRegionRef = useRef(null);
  const shouldAutoScrollRef = useRef(true);

  useEffect(() => {
    const region = messagesRegionRef.current;
    if (!region || !shouldAutoScrollRef.current) return undefined;
    const frame = requestAnimationFrame(() => {
      region.scrollTo({ top: region.scrollHeight, behavior: "smooth" });
    });
    return () => cancelAnimationFrame(frame);
  }, [messages]);

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
    setError(null);
    setExplorerRequest(null);
    setConversationId(crypto.randomUUID());
    setSearchParams({});
    setSidebarOpen(false);
    refreshedNewConversation.current = false;
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
      if (!searchParams.get("conversation") && !refreshedNewConversation.current) {
        refreshedNewConversation.current = true;
        setConversationRefreshKey((current) => current + 1);
      }
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

  function handleQuickAction(label) {
    setDraft("");
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
    <div className="flex h-dvh min-h-0 overflow-hidden bg-base">
      <Sidebar
        open={sidebarOpen}
        onOpen={() => setSidebarOpen(true)}
        onClose={() => setSidebarOpen(false)}
        onNewChat={handleNewChat}
        onCategorySelect={handleCategorySelect}
        onCasesSelect={handleCasesSelect}
        onCaseAnalysis={handleCaseAnalysis}
        conversationRefreshKey={conversationRefreshKey}
        activeConversationId={conversationId}
      />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <TopBar
          language={language}
          onLanguageChange={setLanguage}
          onShare={handleShare}
          shareStatus={shareStatus}
        />

        {messages.length === 0 ? (
          <main className="flex min-h-0 flex-1 flex-col justify-center overflow-hidden bg-[#212121] px-4 py-10 sm:px-6">
            <div className="mx-auto w-full max-w-3xl">
              <ChatComposer
                value={draft}
                onChange={setDraft}
                onSubmit={handleDraftSubmit}
                onSuggestion={handleQuickAction}
                disabled={sending}
                active={false}
              />
            </div>
          </main>
        ) : (
          <div className="flex min-h-0 flex-1 flex-col bg-[#212121]">
            <main
              ref={messagesRegionRef}
              onScroll={(event) => {
                const region = event.currentTarget;
                shouldAutoScrollRef.current =
                  region.scrollHeight - region.scrollTop - region.clientHeight < 96;
              }}
              className="min-h-0 flex-1 overflow-y-auto"
            >
              <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-6 pb-10 sm:px-6">
                {messages.map((message) => (
                  <MessageBubble key={message.id} {...message} onCitationClick={handleCitationClick} />
                ))}
                {sending && <p className="text-sm text-[#9b9b9b]">Thinking…</p>}
                {error && <p className="text-sm text-red-400">{error}</p>}
              </div>
            </main>
            <footer className="shrink-0 bg-[#212121] px-4 pb-[calc(1rem+env(safe-area-inset-bottom))] pt-2 sm:px-6">
              <div className="mx-auto max-w-3xl">
                <ChatComposer
                  value={draft}
                  onChange={setDraft}
                  onSubmit={handleDraftSubmit}
                  onSuggestion={handleQuickAction}
                  disabled={sending}
                  active
                />
              </div>
            </footer>
          </div>
        )}
      </div>

      {explorerRequest && (
        <SourceExplorer request={explorerRequest} onClose={() => setExplorerRequest(null)} />
      )}
    </div>
  );
}

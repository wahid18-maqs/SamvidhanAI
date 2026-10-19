import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ChevronDown,
  ChevronRight,
  Gavel,
  Landmark,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Scale,
  Settings,
  Shield,
  X,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { getConversations } from "../services/api";

const FUNDAMENTAL_RIGHTS_ITEMS = [
  { key: "equality", label: "Right to Equality" },
  { key: "freedom", label: "Right to Freedom" },
  { key: "against_exploitation", label: "Right against Exploitation" },
  { key: "religion", label: "Freedom of Religion" },
  { key: "cultural_educational", label: "Cultural and Educational Rights" },
  { key: "constitutional_remedies", label: "Right to Constitutional Remedies" },
];

const DIRECTIVE_PRINCIPLES_ITEMS = [
  { key: "socialist", label: "Socialist Principles" },
  { key: "gandhian", label: "Gandhian Principles" },
  { key: "liberal_intellectual", label: "Liberal-Intellectual Principles" },
];

function SubItem({ label, onClick, disabled, collapsed = false }) {
  if (collapsed) return null;
  if (disabled) {
    return (
      <span className="block cursor-not-allowed rounded-md px-3 py-1.5 text-left text-xs text-muted/50">
        {label}
      </span>
    );
  }
  return (
    <button
      type="button"
      onClick={onClick}
      className="block w-full rounded-md px-3 py-1.5 text-left text-xs text-muted transition hover:bg-border/60 hover:text-heading"
    >
      {label}
    </button>
  );
}

function NavGroup({ icon: Icon, label, expanded, onToggle, children, collapsed = false }) {
  return (
    <div>
      <button
        type="button"
        onClick={onToggle}
        aria-label={label}
        title={collapsed ? label : undefined}
        className={`flex w-full items-center rounded-lg text-muted transition hover:bg-border/60 hover:text-heading ${
          collapsed ? "justify-center p-2.5" : "gap-2.5 px-3 py-2 text-left text-sm"
        }`}
      >
        <Icon size={16} className="shrink-0" />
        {!collapsed && <span className="flex-1">{label}</span>}
        {!collapsed && (expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />)}
      </button>
      {!collapsed && expanded && <div className="ml-3 space-y-0.5 border-l border-border pl-3 pt-1">{children}</div>}
    </div>
  );
}

function RecentSection({
  conversations,
  loading,
  expanded,
  onToggle,
  showAll,
  onShowMore,
  onSelect,
  activeConversationId,
}) {
  return (
    <section className="flex min-h-0 flex-1 flex-col px-3 pb-4 pt-3">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={expanded}
        className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-medium text-muted transition hover:bg-border/60 hover:text-heading"
      >
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span>Recent</span>
      </button>
      {expanded && (
        <div className="mt-1 min-h-0 flex-1 space-y-0.5 overflow-y-auto">
          {loading ? (
            [1, 2, 3, 4].map((row) => (
              <div key={row} className="h-8 animate-pulse rounded-lg bg-border/40" />
            ))
          ) : conversations.length === 0 ? (
            <p className="px-3 py-2 text-xs text-muted">No conversations yet</p>
          ) : (
            <>
              {(showAll ? conversations : conversations.slice(0, 20)).map((conversation) => (
                <button
                  key={conversation.id}
                  type="button"
                  onClick={() => onSelect(conversation.id)}
                  title={conversation.title || "Untitled conversation"}
                  className={`block w-full truncate rounded-lg px-3 py-2 text-left text-xs transition ${
                    activeConversationId === conversation.id
                      ? "bg-border/70 text-heading"
                      : "text-muted hover:bg-border/50 hover:text-heading"
                  }`}
                >
                  {conversation.title || "Untitled conversation"}
                </button>
              ))}
              {!showAll && conversations.length > 20 && (
                <button
                  type="button"
                  onClick={onShowMore}
                  className="w-full px-3 py-2 text-left text-xs text-muted transition hover:text-heading"
                >
                  Show more
                </button>
              )}
            </>
          )}
        </div>
      )}
    </section>
  );
}

export default function Sidebar({
  open,
  onOpen,
  onClose,
  onNewChat,
  onCategorySelect,
  onCasesSelect,
  onCaseAnalysis,
  onCollapsedChange,
  conversationRefreshKey,
  activeConversationId,
}) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(null);
  const [isCollapsed, setIsCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("samvidhanai-sidebar-collapsed") === "true";
  });
  const [recentExpanded, setRecentExpanded] = useState(() => {
    if (typeof window === "undefined") return true;
    return localStorage.getItem("samvidhanai-recent-expanded") !== "false";
  });
  const [conversations, setConversations] = useState([]);
  const [recentLoading, setRecentLoading] = useState(false);
  const [showAllRecent, setShowAllRecent] = useState(false);

  useEffect(() => {
    localStorage.setItem("samvidhanai-sidebar-collapsed", String(isCollapsed));
    if (isCollapsed) setExpanded(null);
    onCollapsedChange?.(isCollapsed);
  }, [isCollapsed, onCollapsedChange]);

  useEffect(() => {
    localStorage.setItem("samvidhanai-recent-expanded", String(recentExpanded));
  }, [recentExpanded]);

  useEffect(() => {
    let active = true;
    if (!user) {
      setConversations([]);
      setRecentLoading(false);
      return undefined;
    }
    setRecentLoading(true);
    getConversations()
      .then((data) => {
        if (!active) return;
        const sorted = [...(data.conversations || [])].sort(
          (left, right) => new Date(right.updated_at || 0) - new Date(left.updated_at || 0),
        );
        setConversations(sorted);
      })
      .catch(() => active && setConversations([]))
      .finally(() => active && setRecentLoading(false));
    return () => {
      active = false;
    };
  }, [user, conversationRefreshKey]);

  function toggle(name) {
    setExpanded((current) => (current === name ? null : name));
  }

  function selectConversation(id) {
    navigate(`/chat?conversation=${id}`);
    onClose();
  }

  return (
    <>
      {!open && (
        <button
          type="button"
          onClick={onOpen}
          aria-label="Open menu"
          title="Open menu"
          className="fixed left-4 top-3 z-20 flex h-8 w-8 items-center justify-center rounded-full text-muted transition hover:bg-border/60 hover:text-heading lg:hidden"
        >
          <Menu size={20} />
        </button>
      )}
      {open && <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={onClose} aria-hidden="true" />}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex h-screen max-w-[85vw] shrink-0 flex-col border-r border-border bg-panel transition-all duration-200 lg:static lg:z-auto lg:translate-x-0 ${
          isCollapsed ? "w-16 lg:w-16" : "w-72 lg:w-72"
        } ${open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
      >
        <div className={`flex h-16 items-center border-b border-border ${isCollapsed ? "justify-center px-2" : "gap-2.5 px-5"}`}>
          {!isCollapsed && <Landmark size={20} className="shrink-0 text-muted" />}
          {!isCollapsed && <span className="flex-1 font-semibold tracking-wide text-heading">SamvidhanAI</span>}
          <button
            type="button"
            onClick={() => setIsCollapsed((current) => !current)}
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-muted transition hover:bg-border/60 hover:text-heading"
          >
            {isCollapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          </button>
          {!isCollapsed && (
            <button type="button" onClick={onClose} aria-label="Close menu" className="shrink-0 text-muted hover:text-heading lg:hidden">
              <X size={18} />
            </button>
          )}
        </div>

        <div className={isCollapsed ? "p-2" : "p-4"}>
          <button
            type="button"
            onClick={onNewChat}
            title="New Chat"
            aria-label="New Chat"
            className={`flex items-center rounded-lg text-sm font-medium text-body transition hover:bg-border/60 hover:text-heading ${
              isCollapsed ? "h-10 w-10 justify-center p-0" : "w-full gap-3 px-3 py-2.5"
            }`}
          >
            <span className="text-lg leading-none">+</span>
            {!isCollapsed && <span>New Chat</span>}
          </button>
        </div>

        <div className="min-h-0 flex-1 flex flex-col">
          <nav className="flex-none space-y-1.5 px-3 py-2">
            <NavGroup
              icon={Shield}
              label="Fundamental Rights"
              expanded={expanded === "fundamental_rights"}
              onToggle={() => toggle("fundamental_rights")}
              collapsed={isCollapsed}
            >
              {FUNDAMENTAL_RIGHTS_ITEMS.map((item) => (
                <SubItem key={item.key} label={item.label} onClick={() => onCategorySelect(item.key, item.label)} />
              ))}
            </NavGroup>
            <NavGroup
              icon={Scale}
              label="Directive Principles"
              expanded={expanded === "directive_principles"}
              onToggle={() => toggle("directive_principles")}
              collapsed={isCollapsed}
            >
              {DIRECTIVE_PRINCIPLES_ITEMS.map((item) => (
                <SubItem key={item.key} label={item.label} onClick={() => onCategorySelect(item.key, item.label)} />
              ))}
            </NavGroup>
            <NavGroup
              icon={Gavel}
              label="Case Studies"
              expanded={expanded === "case_studies"}
              onToggle={() => toggle("case_studies")}
              collapsed={isCollapsed}
            >
              <SubItem label="Landmark Judgments" onClick={onCasesSelect} />
              <SubItem label="Case Analysis" onClick={onCaseAnalysis} />
            </NavGroup>
          </nav>

          {!isCollapsed && (
            <RecentSection
              conversations={conversations}
              loading={recentLoading}
              expanded={recentExpanded}
              onToggle={() => setRecentExpanded((current) => !current)}
              showAll={showAllRecent}
              onShowMore={() => setShowAllRecent(true)}
              onSelect={selectConversation}
              activeConversationId={activeConversationId}
            />
          )}
        </div>

        <div className={isCollapsed ? "space-y-1.5 px-2 pb-4" : "space-y-1.5 px-3 pb-4"}>
          <Link
            to="/settings"
            aria-label="Settings"
            title="Settings"
            className={`flex w-full items-center rounded-lg text-muted transition hover:bg-border/60 hover:text-heading ${
              isCollapsed ? "justify-center p-2.5" : "gap-2.5 px-3 py-2 text-left text-sm"
            }`}
          >
            <Settings size={16} className="shrink-0" />
            {!isCollapsed && "Settings"}
          </Link>
        </div>
      </aside>
    </>
  );
}

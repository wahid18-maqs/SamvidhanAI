import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BookOpen,
  ChevronDown,
  ChevronRight,
  Gavel,
  Landmark,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Scale,
  Search,
  Settings,
  Shield,
  X,
} from "lucide-react";

// NB: the Ashoka State Emblem shown in the reference mockup is a protected
// national symbol (State Emblem of India (Prohibition of Improper Use) Act,
// 2005) and must not be reproduced as an app logo. `Landmark` is used as a
// deliberate, license-safe substitute per Ui updates and features.md 1.7.

// Fundamental Rights / Directive Principles category keys mirror
// backend/article_categories.py's ARTICLE_CATEGORIES exactly.
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
      <span
        title="Coming soon"
        className="block cursor-not-allowed rounded-md px-3 py-1.5 text-left text-xs text-muted/50"
      >
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
  if (collapsed) {
    return (
      <div>
        <button
          type="button"
          onClick={onToggle}
          aria-label={label}
          title={label}
          className="flex w-full items-center justify-center rounded-lg p-2.5 text-muted transition hover:bg-border/60 hover:text-heading"
        >
          <Icon size={16} className="shrink-0" />
        </button>
      </div>
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-muted transition hover:bg-border/60 hover:text-heading"
      >
        <Icon size={16} className="shrink-0" />
        <span className="flex-1">{label}</span>
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      {expanded && <div className="ml-3 space-y-0.5 border-l border-border pl-3 pt-1">{children}</div>}
    </div>
  );
}

export default function Sidebar({
  open,
  onClose,
  onNewChat,
  onCategorySelect,
  onCasesSelect,
  onArticleNumber,
  onTopicSearch,
  onFulltextSearch,
  onCaseAnalysis,
}) {
  const [expanded, setExpanded] = useState(null); // which single group is open, or null
  const [isCollapsed, setIsCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("samvidhanai-sidebar-collapsed") === "true";
  });
  const [articleNumber, setArticleNumber] = useState("");
  const [topicQuery, setTopicQuery] = useState("");
  const [fulltextQuery, setFulltextQuery] = useState("");

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("samvidhanai-sidebar-collapsed", String(isCollapsed));
    }
  }, [isCollapsed]);

  useEffect(() => {
    if (isCollapsed) {
      setExpanded(null);
    }
  }, [isCollapsed]);

  function toggle(name) {
    setExpanded((current) => (current === name ? null : name));
  }

  function submitArticleNumber(event) {
    event.preventDefault();
    const trimmed = articleNumber.trim();
    if (!trimmed) return;
    onArticleNumber(trimmed);
  }

  function submitTopicSearch(event) {
    event.preventDefault();
    const trimmed = topicQuery.trim();
    if (!trimmed) return;
    onTopicSearch(trimmed);
  }

  function submitFulltextSearch(event) {
    event.preventDefault();
    const trimmed = fulltextQuery.trim();
    if (!trimmed) return;
    onFulltextSearch(trimmed);
  }

  return (
    <>
      {/* Backdrop: mobile-only, closes the drawer on outside tap. The
          sidebar itself is lg:static (a normal flex-row item, always
          visible) but fixed/overlaid below lg, so this only ever renders
          stacked behind it on small screens. */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex h-screen max-w-[85vw] shrink-0 flex-col border-r border-border bg-panel transition-all duration-200 lg:static lg:z-auto lg:translate-x-0 ${
          isCollapsed ? "w-16 lg:w-16" : "w-72 lg:w-72"
        } ${open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
      >
        <div className={`flex h-16 items-center border-b border-border ${isCollapsed ? "justify-center px-2" : "gap-2.5 px-5"}`}>
          {!isCollapsed && <Landmark size={20} className="shrink-0 text-gold" />}
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
            <button
              type="button"
              onClick={onClose}
              aria-label="Close menu"
              className="shrink-0 text-muted hover:text-heading lg:hidden"
            >
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
          className={`flex items-center justify-center rounded-xl bg-gold-gradient shadow-lg transition hover:opacity-95 ${
            isCollapsed ? "h-10 w-10 p-0" : "w-full gap-2.5 px-4 py-2.5 text-sm font-medium text-base"
          }`}
        >
          <span className={isCollapsed ? "text-lg leading-none" : undefined}>+</span>
          {!isCollapsed && <span>New Chat</span>}
        </button>
      </div>

      <nav className="flex-1 space-y-1.5 overflow-y-auto px-3 py-2">
        <NavGroup
          icon={Search}
          label="Search Articles"
          expanded={expanded === "search"}
          onToggle={() => toggle("search")}
          collapsed={isCollapsed}
        >
          {!isCollapsed && (
            <>
              <form onSubmit={submitArticleNumber} className="flex gap-1.5 px-3 py-1.5">
                <input
                  type="text"
                  inputMode="numeric"
                  value={articleNumber}
                  onChange={(event) => setArticleNumber(event.target.value)}
                  placeholder="Article #"
                  className="w-full min-w-0 rounded-md border border-border bg-base px-2 py-1 text-xs text-heading placeholder-muted focus:border-gold focus:outline-none"
                />
                <button
                  type="submit"
                  className="shrink-0 rounded-md bg-gold-gradient px-2.5 py-1 text-xs font-medium text-base"
                >
                  Go
                </button>
              </form>
              <form onSubmit={submitTopicSearch} className="flex gap-1.5 px-3 py-1.5">
                <input
                  type="text"
                  value={topicQuery}
                  onChange={(event) => setTopicQuery(event.target.value)}
                  placeholder="Search by topic…"
                  className="w-full min-w-0 rounded-md border border-border bg-base px-2 py-1 text-xs text-heading placeholder-muted focus:border-gold focus:outline-none"
                />
                <button
                  type="submit"
                  className="shrink-0 rounded-md bg-gold-gradient px-2.5 py-1 text-xs font-medium text-base"
                >
                  Go
                </button>
              </form>
              <form onSubmit={submitFulltextSearch} className="flex gap-1.5 px-3 py-1.5">
                <input
                  type="text"
                  value={fulltextQuery}
                  onChange={(event) => setFulltextQuery(event.target.value)}
                  placeholder="Exact phrase…"
                  className="w-full min-w-0 rounded-md border border-border bg-base px-2 py-1 text-xs text-heading placeholder-muted focus:border-gold focus:outline-none"
                />
                <button
                  type="submit"
                  className="shrink-0 rounded-md bg-gold-gradient px-2.5 py-1 text-xs font-medium text-base"
                >
                  Go
                </button>
              </form>
            </>
          )}
        </NavGroup>

        <NavGroup
          icon={Shield}
          label="Fundamental Rights"
          expanded={expanded === "fundamental_rights"}
          onToggle={() => toggle("fundamental_rights")}
          collapsed={isCollapsed}
        >
          {!isCollapsed &&
            FUNDAMENTAL_RIGHTS_ITEMS.map((item) => (
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
          {!isCollapsed &&
            DIRECTIVE_PRINCIPLES_ITEMS.map((item) => (
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
          {!isCollapsed && (
            <>
              <SubItem label="Landmark Judgments" onClick={onCasesSelect} />
              <SubItem label="Case Analysis" onClick={onCaseAnalysis} />
            </>
          )}
        </NavGroup>
      </nav>

      {!isCollapsed && (
        <div className="space-y-1.5 px-3 pb-4">
          <Link
            to="/history"
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-muted transition hover:bg-border/60 hover:text-heading"
          >
            <BookOpen size={16} className="shrink-0" />
            History
          </Link>
          <Link
            to="/settings"
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-muted transition hover:bg-border/60 hover:text-heading"
          >
            <Settings size={16} className="shrink-0" />
            Settings
          </Link>
        </div>
      )}

      {isCollapsed && (
        <div className="space-y-1.5 px-2 pb-4">
          <Link
            to="/history"
            aria-label="History"
            title="History"
            className="flex w-full items-center justify-center rounded-lg p-2.5 text-muted transition hover:bg-border/60 hover:text-heading"
          >
            <BookOpen size={16} className="shrink-0" />
          </Link>
          <Link
            to="/settings"
            aria-label="Settings"
            title="Settings"
            className="flex w-full items-center justify-center rounded-lg p-2.5 text-muted transition hover:bg-border/60 hover:text-heading"
          >
            <Settings size={16} className="shrink-0" />
          </Link>
        </div>
      )}
    </aside>
    </>
  );
}

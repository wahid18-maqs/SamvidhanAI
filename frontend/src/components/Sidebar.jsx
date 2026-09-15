import { useState } from "react";
import { Link } from "react-router-dom";
import {
  BookOpen,
  ChevronDown,
  ChevronRight,
  Gavel,
  Landmark,
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

function SubItem({ label, onClick, disabled }) {
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

function NavGroup({ icon: Icon, label, expanded, onToggle, children }) {
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
  const [articleNumber, setArticleNumber] = useState("");
  const [topicQuery, setTopicQuery] = useState("");
  const [fulltextQuery, setFulltextQuery] = useState("");

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
        className={`fixed inset-y-0 left-0 z-40 flex h-screen w-72 max-w-[85vw] shrink-0 flex-col border-r border-border bg-panel transition-transform duration-200 lg:static lg:z-auto lg:w-72 lg:max-w-none lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-16 items-center gap-2.5 border-b border-border px-5">
          <Landmark size={20} className="shrink-0 text-gold" />
          <span className="flex-1 font-semibold tracking-wide text-heading">SamvidhanAI</span>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close menu"
            className="shrink-0 text-muted hover:text-heading lg:hidden"
          >
            <X size={18} />
          </button>
        </div>

      <div className="p-4">
        <button
          type="button"
          onClick={onNewChat}
          className="flex w-full items-center justify-center gap-2.5 rounded-xl bg-gold-gradient px-4 py-2.5 text-sm font-medium text-base shadow-lg transition hover:opacity-95"
        >
          + New Chat
        </button>
      </div>

      <nav className="flex-1 space-y-1.5 overflow-y-auto px-3 py-2">
        <NavGroup
          icon={Search}
          label="Search Articles"
          expanded={expanded === "search"}
          onToggle={() => toggle("search")}
        >
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
        </NavGroup>

        <NavGroup
          icon={Shield}
          label="Fundamental Rights"
          expanded={expanded === "fundamental_rights"}
          onToggle={() => toggle("fundamental_rights")}
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
        >
          <SubItem label="Landmark Judgments" onClick={onCasesSelect} />
          <SubItem label="Case Analysis" onClick={onCaseAnalysis} />
        </NavGroup>
      </nav>

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
    </aside>
    </>
  );
}

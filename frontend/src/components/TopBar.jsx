import { Share2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import LanguageSelector from "./LanguageSelector";

export default function TopBar({
  language,
  onLanguageChange,
  onShare,
  shareStatus,
}) {
  const { user, signOut } = useAuth();

  return (
    <header className="bg-transparent">
      <div className="flex h-14 items-center gap-3 px-4 sm:gap-4 sm:px-6">
        <div className="min-w-0 flex-1" />

        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          {shareStatus && <span className="hidden text-xs text-muted sm:inline">{shareStatus}</span>}
          <button
            type="button"
            onClick={onShare}
            title="Share"
            className="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium text-body transition hover:bg-border/60 sm:px-3"
          >
            <Share2 size={14} />
            <span className="hidden sm:inline">Share</span>
          </button>
          <LanguageSelector value={language} onChange={onLanguageChange} />
          <button
            type="button"
            title={user?.email}
            onClick={signOut}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#4a4a4a] text-xs font-semibold text-heading"
          >
            {user?.email?.[0]?.toUpperCase() ?? "?"}
          </button>
        </div>
      </div>

    </header>
  );
}

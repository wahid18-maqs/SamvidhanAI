import { useEffect, useRef } from "react";
import { ArrowUp, FileText, Scale, Search, Shield } from "lucide-react";

const SUGGESTIONS = [
  { label: "Preamble", icon: FileText },
  { label: "Fundamental Rights", icon: Shield },
  { label: "Emergency Provisions", icon: Scale },
  { label: "President of India", icon: Search },
];

export default function ChatComposer({ value, onChange, onSubmit, onSuggestion, disabled, active }) {
  const textareaRef = useRef(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 144)}px`;
  }, [value]);

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSubmit(event);
    }
  }

  return (
    <div
      className={`w-full transition-all duration-500 ease-out ${
        active ? "max-w-3xl" : "max-w-3xl"
      }`}
    >
      {!active && (
        <h1 className="mb-8 text-center text-2xl font-medium tracking-tight text-[#ececec] sm:text-3xl">
          What would you like to know about the Constitution?
        </h1>
      )}

      <form onSubmit={onSubmit} className="w-full">
        <div className="flex min-h-14 items-end gap-3 rounded-[28px] bg-[#2f2f2f] px-4 py-2 shadow-[0_8px_30px_rgba(0,0,0,0.18)] transition-colors focus-within:bg-[#383838]">
          <textarea
            ref={textareaRef}
            rows={1}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything"
            aria-label="Ask anything"
            disabled={disabled}
            className="max-h-36 min-h-10 flex-1 resize-none overflow-y-auto bg-transparent py-2.5 text-[15px] leading-5 text-[#ececec] outline-none placeholder:text-[#9b9b9b] disabled:cursor-not-allowed disabled:opacity-60"
          />
          <button
            type="submit"
            aria-label="Send message"
            title="Send message"
            disabled={disabled || !value.trim()}
            className="mb-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#ececec] text-[#202020] transition hover:bg-white disabled:cursor-not-allowed disabled:bg-[#676767] disabled:text-[#343434]"
          >
            <ArrowUp size={18} strokeWidth={2.5} />
          </button>
        </div>
      </form>

      {!active && (
        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {SUGGESTIONS.map(({ label, icon: Icon }) => (
            <button
              key={label}
              type="button"
              onClick={() => onSuggestion(label)}
              disabled={disabled}
              className="flex min-h-10 items-center gap-2 rounded-xl px-3 py-2 text-left text-xs text-[#b5b5b5] transition hover:bg-[#2a2a2a] hover:text-[#ececec] disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Icon size={15} className="shrink-0" />
              <span>{label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

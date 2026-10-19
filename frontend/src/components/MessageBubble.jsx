import { useState } from "react";
import { ThumbsDown, ThumbsUp } from "lucide-react";
import CitationChip from "./CitationChip";
import { postFeedback } from "../services/api";

function CitationRow({ citations, onCitationClick }) {
  if (!citations?.length) return null;
  return (
    <div className="mt-1 flex flex-wrap gap-1.5">
      {citations.map((citation) => (
        <CitationChip key={citation.source_id} citation={citation} onClick={onCitationClick} />
      ))}
    </div>
  );
}

/** Section 1.4 footer: thumbs up/down feedback on one assistant message.
 * ("Cite Source" isn't a separate button here — the inline citation chips
 * already open the Source Explorer, which serves the same purpose.) Hidden
 * entirely on a read-only view (e.g. a shared conversation), since giving
 * feedback requires being the message's own authenticated owner. */
function FeedbackRow({ messageId }) {
  const [choice, setChoice] = useState(null);
  const [error, setError] = useState(null);

  async function choose(feedback) {
    if (choice || !messageId) return;
    setChoice(feedback);
    try {
      await postFeedback(messageId, feedback);
    } catch (err) {
      setChoice(null);
      setError(err.message || "Could not send feedback.");
    }
  }

  return (
    <div className="flex items-center gap-3 pt-1">
      <button
        type="button"
        onClick={() => choose("positive")}
        disabled={choice !== null}
        aria-label="Helpful"
        className={`rounded-full p-1.5 transition hover:bg-border/60 ${choice === "positive" ? "text-heading" : "text-muted hover:text-heading"}`}
      >
        <ThumbsUp size={15} />
      </button>
      <button
        type="button"
        onClick={() => choose("negative")}
        disabled={choice !== null}
        aria-label="Not helpful"
        className={`rounded-full p-1.5 transition hover:bg-border/60 ${choice === "negative" ? "text-heading" : "text-muted hover:text-heading"}`}
      >
        <ThumbsDown size={15} />
      </button>
      {choice && <span className="text-xs text-muted">Thanks for the feedback.</span>}
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  );
}

/** Per Section 1.4: user messages are right-aligned bubbles; AI
 * messages flow left-aligned with no bubble, structured as Summary ->
 * section headers -> Key Clauses -> Explanation, each citation attached to
 * the specific piece of content it supports. History-loaded messages carry
 * the same structure (persisted alongside the flat `content`, see
 * backend/api/routes/chat.py's structured_answer column) so this renders
 * identically live or reloaded. Falls back to flat `content` only for a
 * message that genuinely has no structure (e.g. a message persisted before
 * the structured_answer column existed). */
export default function MessageBubble({
  id,
  role,
  content,
  summary,
  sections,
  keyClauses,
  explanation,
  citations,
  onCitationClick,
  readOnly,
}) {
  if (role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[70%] rounded-3xl bg-[#383838] px-4 py-2.5 text-[15px] text-heading">
          {content}
        </div>
      </div>
    );
  }

  const hasStructure = summary || sections?.length || keyClauses?.length || explanation;
  if (!hasStructure) {
    return (
      <div className="max-w-3xl space-y-4 text-[15px] leading-7 text-body">
        <p className="whitespace-pre-wrap">{content}</p>
        <CitationRow citations={citations} onCitationClick={onCitationClick} />
        {!readOnly && <FeedbackRow messageId={id} />}
      </div>
    );
  }

  const isShortReply = !sections?.length && !keyClauses?.length && explanation?.includes("This is a research aid, not legal advice.");

  return (
    <div className="max-w-3xl space-y-5 text-[15px] leading-7 text-body">
      {summary && (
        <p>
          {!isShortReply && <span className="font-semibold text-heading">Summary: </span>}
          {summary}
        </p>
      )}

      {sections?.map((section, index) => (
        <div key={index}>
          <h3 className="font-semibold text-heading">{section.heading}</h3>
          <p className="mt-1 whitespace-pre-wrap">{section.body}</p>
          <CitationRow citations={section.citations} onCitationClick={onCitationClick} />
        </div>
      ))}

      {keyClauses?.length > 0 && (
        <div>
          <h3 className="font-semibold text-heading">Key Clauses</h3>
          <ul className="mt-2 list-disc space-y-2 pl-5">
            {keyClauses.map((clause, index) => (
              <li key={index}>
                {clause.text}
                <CitationRow citations={clause.citations} onCitationClick={onCitationClick} />
              </li>
            ))}
          </ul>
        </div>
      )}

      {explanation && !isShortReply && (
        <div>
          <h3 className="font-semibold text-heading">Explanation</h3>
          <p className="mt-1 whitespace-pre-wrap text-body-muted">{explanation}</p>
        </div>
      )}

      {isShortReply && <p className="text-xs leading-5 text-muted">{explanation}</p>}

      {!readOnly && <FeedbackRow messageId={id} />}
    </div>
  );
}

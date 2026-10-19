/** Inline citation chip (Section 1.4: "e.g. [Art. 368, Clause 2] — clickable,
 * opens Source Explorer scoped to that citation"). */
export default function CitationChip({ citation, onClick }) {
  return (
    <button
      type="button"
      onClick={() => onClick(citation)}
      className="inline-flex items-center rounded-full bg-border px-2 py-0.5 text-xs font-medium text-body transition hover:bg-border-strong"
    >
      {citation.label}
    </button>
  );
}

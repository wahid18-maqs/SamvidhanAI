# Case-law ingestion — pending work

> Tracks the remaining case-law ingestion for the cases listed in
> `backend/case_law.py`'s `PENDING_CASE_METADATA`. Nothing here is
> ingested yet — this file exists so the work is easy to pick back up
> once source text is available, without re-deriving the plan from
> scratch.

## Status

**6 of 10 cases ingested and indexed** (2026-09-15): `minerva_mills_1980`,
`puttaswamy_2017`, `adr_v_election_commission_2024`,
`state_of_punjab_v_davinder_singh_2024`, `property_owners_association_2024`,
`pooja_ramesh_singh_v_jk_bank_2026` are now in `CASE_METADATA`, chunked,
indexed in Pinecone, spot-checked via retrieval, and have benchmark
questions (`q33`–`q38` in `evaluation/datasets/retrieval_questions.json`).

**4 cases blocked on re-sourcing — wrong PDF was supplied for each.**
Caught by comparing each extracted PDF's own header/citation against the
expected case, before chunking/indexing:

| case_id | Expected | PDF actually contains |
|---|---|---|
| `golaknath_1967` | I.C. Golaknath v. State of Punjab (1967) | Assam Sanmilita Mahasangha v. Union of India (2014) |
| `kesavananda_bharati_1973` | Kesavananda Bharati v. State of Kerala (1973) | Maharao Sahib Shri Bhim Singhji v. Union of India (1980) |
| `sr_bommai_1994` | S.R. Bommai v. Union of India (1994) | A 2008 Kerala HC sales-tax writ order (~1.5KB of text) |
| `in_re_article_370_2023` | In Re: Article 370 final judgment (Dec 11, 2023) | A procedural "Record of Proceedings" from an Aug 8, 2023 hearing, not the substantive judgment |

Their (wrong) extracted text was moved to
`data/processed/case_law/_wrong_source/` so `scripts/chunk_case_law.py`'s
glob can never pick it up by accident. Their entries in
`PENDING_CASE_METADATA` carry a `note` describing the mismatch. **Do not
re-run extraction/chunking/indexing for these 4 until the correct source
PDF replaces the current file at `data/raw/case_law/<case_id>.pdf`.**

Indian Kanoon API access has been applied for but not yet granted (see
`KNOWN_ISSUES.md`'s deferred Phase 2.5 entry) — until then, sourcing is
manual per case.

## Cases still pending

| case_id | Case | Year | Related articles | Notes |
|---|---|---|---|---|
| `kesavananda_bharati_1973` | Kesavananda Bharati v. State of Kerala | 1973 | 368, 13, 19, 31 | Basic structure doctrine. BLOCKED — see table above |
| `golaknath_1967` | I.C. Golaknath v. State of Punjab | 1967 | 368, 13 | BLOCKED — see table above |
| `sr_bommai_1994` | S.R. Bommai v. Union of India | 1994 | 356 | BLOCKED — see table above |
| `in_re_article_370_2023` | In Re: Article 370 of the Constitution | 2023 | 370, 356 | BLOCKED — see table above |

## Ingestion pipeline (proven on 8 cases now: the original 2 + these 6)

For each case, once source text is in hand:

1. Save the source PDF/text into `data/raw/case_law/<case_id>.pdf` (or
   `.txt`) — filename stem must match the `case_id` key in
   `backend/case_law.py`. Extension must be lowercase `.pdf` —
   `scripts/ingest.py`'s glob is case-sensitive on Linux.
2. Run `scripts/ingest.py` to extract text into
   `data/processed/case_law/<case_id>.txt`.
   **Before proceeding, open the extracted `.txt` and check its own
   header/citation line against the case you expect** — two rounds of
   this ingestion have turned up wrong-PDF mismatches (see table above)
   that would otherwise silently index the wrong judgment under the
   right case name.
3. Move the case's entry from `PENDING_CASE_METADATA` to `CASE_METADATA`
   in `backend/case_law.py` — `scripts/chunk_case_law.py` reads case
   metadata from `CASE_METADATA`, so this must happen before chunking or
   the chunk metadata will come out flagged
   `metadata_extraction_failed: true`.
4. Run `scripts/chunk_case_law.py` to chunk by paragraph number (falls
   back to fixed windows if the judgment isn't cleanly numbered) and
   write `data/processed/chunks/case_law/<case_id>.jsonl` +
   `data/processed/metadata/case_law/<case_id>.jsonl`.
5. Run `PYTHONPATH=. python3 scripts/index.py` to embed and upsert into
   Pinecone under `document_type: "case_law"`. (Run
   `... --dry-run` first to sanity-check record counts before writing.)
   Note: this script re-processes every chunk file under
   `data/processed/chunks/`, not just the new case — re-upserting
   already-indexed content is a harmless no-op by `_id`, just adds time.
6. Spot-check retrieval: query the case by name and by a related article
   number, confirm it comes back with a sensible top-K hit.
7. Add at least one benchmark question to
   `evaluation/datasets/retrieval_questions.json` for the newly-ingested
   case (per `KNOWN_ISSUES.md`'s eval-coverage note).

## Notes on the specific list

- Several 2023–2026 cases were flagged "verify exact case title/citation
  before indexing" in earlier drafts of this doc — those have now been
  confirmed correct (citation lines matched, see the 6 ingested above)
  except the 4 still blocked on a wrong PDF.
- `pooja_ramesh_singh_v_jk_bank_2026`'s note ("AI hallucinated
  precedents ruling") reflects that this case is itself *about* an AI
  generating fake citations — that framing was retained in its
  `CASE_METADATA` entry.
- Where an official SCI JUDIS PDF exists for a case, prefer it as the
  source (same reasoning as the first 2 cases) — Indian Kanoon (once API
  access is granted) is the fetch mechanism, not a replacement for
  citing the canonical source per `KNOWN_ISSUES.md`.

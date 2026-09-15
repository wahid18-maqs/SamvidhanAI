# Case-law ingestion

> Tracks case-law ingestion for the cases in `backend/case_law.py`.
> Historical record of past mismatches is kept below so the same
> failure mode is easier to recognize if it recurs.

## Status (2026-09-15)

**All 10 originally-planned cases are now ingested and indexed**, on top
of the original 2 (`maneka_gandhi_1978`, `shreya_singhal_2015`) — 12
cases total, all in `CASE_METADATA`. `PENDING_CASE_METADATA` is empty.

The last 4 — `golaknath_1967`, `kesavananda_bharati_1973`,
`sr_bommai_1994`, `in_re_article_370_2023` — went through two rounds:

1. **First PDFs supplied were wrong** (see "Past incident" below).
2. **Re-sourced and re-verified** against official/authoritative text
   before replacing:

   | case_id | Source used | Verified via |
   |---|---|---|
   | `golaknath_1967` | Indian Kanoon PDF export (`indiankanoon.org/doc/120358/?type=pdf`) | Header: "I.C. GOLAKNATH & ORS. vs STATE OF PUNJAB", 1967 AIR 1643, judgment date 27/02/1967 |
   | `kesavananda_bharati_1973` | SC Observer PDF mirror (`scobserver.in`) | Header: "Kesavananda Bharati Sripadagalvaru and Ors vs State of Kerala and Anr", W.P. (civil) 135/1970, judgment date 24/04/1973, 502 pages |
   | `sr_bommai_1994` | CJP.org.in PDF reproduction | Header: "S.R. BOMMAI vs UNION OF INDIA", 1994 AIR 1918, (1994) 3 SCC 1, judgment date 11/03/1994 |
   | `in_re_article_370_2023` | Indian Kanoon PDF export (`indiankanoon.org/doc/77326406/?type=pdf`) | Header: "IN RE: ARTICLE 370 OF THE CONSTITUTION", 2023 INSC 1058, W.P. (Civil) No. 1099/2019, judgment date **11 December 2023** (confirmed, not the Aug 2023 procedural roster), 390 pages |

   Note on sourcing priority: the official `sci.gov.in`/`api.sci.gov.in`
   JUDIS archive was tried first for all 4. It resolved and downloaded for
   Bommai (`api.sci.gov.in/jonew/judis/11570.pdf`), but that copy is an
   **image-only scan with no extractable text layer** — unusable by this
   project's pypdf-based `scripts/ingest.py`. The official Article 370
   host (`webapi.sci.gov.in`) was unreachable from the dev sandbox
   (DNS resolves, connection times out) at the time of ingestion — worth
   retrying from a different network if a primary-source copy is wanted
   later. Fell back to text-searchable third-party reproductions per the
   documented fallback priority (official → government repository →
   Indian Kanoon).

The 4 wrong original PDFs are preserved (never deleted) at
`data/incorrect_pdfs_backup/`.

### Benchmark results after re-ingestion

Ran `evaluation/runners/run_retrieval_eval.py --live` (42 questions, incl.
new `q39`-`q42` for these 4 cases) through the real `analyze_query ->
build_metadata_filter -> retrieve` path:

- `explicit-article` (16 q): 100% Recall@10 / 100% Precision@10
- `conceptual` (12 q): 100% Recall@10 / 17.4% Precision@10 (low precision
  here is a pre-existing, separately-tracked characteristic of blended
  constitution+case-law retrieval, not something this ingestion changed)
- `case-law` (14 q): 78.6% Recall@10 / 60.7% Precision@10 — **`q39`
  (Golaknath) and `q40` (Kesavananda Bharati) scored 0% recall**; all
  other case-law questions, including `q41` (Bommai) and `q42`
  (Article 370), passed at 100% recall.

**The `q39`/`q40` misses are a retrieval-routing gap, not a data
problem.** Direct Pinecone fetches confirm both cases are correctly
indexed with accurate `case_id`/`case_name` metadata, and a raw
`search_text` call against Pinecone directly (bypassing the app's graph)
ranks each at #1 given a query built from its own distinctive vocabulary.
The miss happens one layer up: `backend/graph/nodes/analyzer.py`'s
`classify_intent` already recognizes "golaknath" and "kesavananda
bharati" as known case names and routes to the `case_law` intent, but
`backend/graph/nodes/metadata.py`'s `build_metadata_filter` only narrows
the search to `document_type: case_law` for that intent — it never
narrows to the *specific* `case_id` the analyzer detected. So a case-law
query searches the entire case-law corpus by embedding similarity alone,
and a large judgment that discusses the same doctrine at length can crowd
a smaller one out of the top 10 (Kesavananda Bharati's ~3,586 chunks
extensively re-quote and discuss Golak Nath's holding while overturning
it; conversely, Minerva Mills/Property Owners Association/Puttaswamy all
discuss "basic structure" and crowd out Kesavananda Bharati itself for a
generic basic-structure query).

This is **pre-existing and not introduced by this ingestion round** — the
same failure mode also hits `q29` (Maneka Gandhi, one of the original 2
cases indexed months before this work, 0% recall in this same eval run).
Neither `backend/graph/nodes/analyzer.py` nor
`backend/graph/nodes/metadata.py` was touched by this ingestion — only
`backend/case_law.py`'s data dict and the eval dataset changed — so
`q29`'s failure isolates the cause to the routing gap itself rather than
anything specific to the 4 newly-ingested cases. Worth a follow-up: have
`build_metadata_filter` (or a new node) pass through a `case_id` `$eq`
filter when the analyzer's known-case-name match identifies exactly one
case, rather than relying on embedding similarity alone to disambiguate
between same-topic judgments.

## Past incident: wrong PDFs supplied (resolved 2026-09-15)

The first PDFs dropped into `data/raw/case_law/` for these 4 case_ids
were **not the correct document** — caught by reading each extracted
`.txt`'s own header/citation against the expected case, before
chunking/indexing (so nothing wrong ever reached Pinecone):

| case_id | Expected | What the wrong PDF actually contained |
|---|---|---|
| `golaknath_1967` | I.C. Golak Nath v. State of Punjab (1967) | Assam Sanmilita Mahasangha v. Union of India (2014) |
| `kesavananda_bharati_1973` | Kesavananda Bharati v. State of Kerala (1973) | Maharao Sahib Shri Bhim Singhji v. Union of India (1980) |
| `sr_bommai_1994` | S.R. Bommai v. Union of India (1994) | A 2008 Kerala HC sales-tax writ order (~1.5KB of text) |
| `in_re_article_370_2023` | Article 370 final judgment (11 Dec 2023) | A procedural "Record of Proceedings" from an Aug 8, 2023 hearing |

**Takeaway for future ingestion:** never trust the filename alone —
always open the extracted text and check its own header/citation line
against the case you expect before moving it into `CASE_METADATA` or
chunking it.

## Ingestion pipeline (now proven on all 12 cases)

For each new case, once source text is in hand:

1. Save the source PDF into `data/raw/case_law/<case_id>.pdf` — filename
   stem must match the `case_id` key in `backend/case_law.py`. Extension
   must be lowercase `.pdf` — `scripts/ingest.py`'s glob is
   case-sensitive on Linux.
2. Run `scripts/ingest.py` to extract text into
   `data/processed/case_law/<case_id>.txt`.
   **Before proceeding, open the extracted `.txt` and check its own
   header/citation line against the case you expect** — see the past
   incident above.
3. Move the case's entry from `PENDING_CASE_METADATA` to `CASE_METADATA`
   in `backend/case_law.py` — `scripts/chunk_case_law.py` reads case
   metadata from `CASE_METADATA`, so this must happen before chunking or
   the chunk metadata comes out flagged `metadata_extraction_failed: true`.
4. Run `scripts/chunk_case_law.py` to chunk by paragraph number (falls
   back to fixed windows if the judgment isn't cleanly numbered).
5. Run `PYTHONPATH=. python3 scripts/index.py --dry-run` first to
   sanity-check record counts, then without `--dry-run` to embed and
   upsert into Pinecone. Note: this script re-processes every chunk file
   under `data/processed/chunks/`, not just the new case — re-upserting
   already-indexed content is a harmless no-op by `_id`, just adds time.
   Requires the `pinecone` package installed locally
   (`pip3 install --user --break-system-packages pinecone==6.0.2
   pinecone-plugin-interface==0.0.7` — this is a Debian externally-managed
   Python with no project venv).
6. Spot-check retrieval: query the case by name and by a related article
   number, confirm it comes back with a sensible top-K hit and correct
   `case_id` metadata.
7. Add at least one benchmark question to
   `evaluation/datasets/retrieval_questions.json` for the newly-ingested
   case.

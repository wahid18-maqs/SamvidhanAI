"""Case-law metadata: single source of truth for both ingestion
(scripts/chunk_case_law.py) and runtime lookups (backend/api/routes/
sources.py's related_cases field). Per-file metadata isn't reliably
recoverable from body text alone, so it's tracked here explicitly.

`related_articles` drives the Source Explorer's "Landmark judgments"
section: looking up an article reverse-looks-up any case here whose
related_articles includes it.

IMPORTANT: CASE_METADATA must only contain cases that are actually
ingested and indexed in Pinecone. A case listed here with no
corresponding indexed content will silently break the Source Explorer's
reverse-lookup. Add an entry here only after scripts/index.py has confirmed
the case's vectors are live. Cases identified but not yet ingested go in
PENDING_CASE_METADATA below instead.
"""

CASE_METADATA = {
	"maneka_gandhi_1978": {
		"case_name": "Maneka Gandhi v. Union of India",
		"year": 1978,
		"court": "Supreme Court of India",
		"related_articles": ["21"],
		"analysis": (
			"Maneka Gandhi's passport was impounded without being told why or "
			"given a hearing. The Court read Articles 14, 19, and 21 together "
			"for the first time, holding that any procedure depriving someone "
			"of life or personal liberty must be fair, just, and reasonable -- "
			"not merely enacted by the legislature. This overturned the older, "
			"narrower reading of Article 21 from A.K. Gopalan (1950) and is "
			"the foundation for later expansions of the right to life to "
			"include privacy, livelihood, a clean environment, and more."
		),
	},
	"shreya_singhal_2015": {
		"case_name": "Shreya Singhal v. Union of India",
		"year": 2015,
		"court": "Supreme Court of India",
		"related_articles": ["19"],
		"analysis": (
			"Challenged Section 66A of the IT Act, which criminalized sending "
			"'offensive' messages online in vague, undefined terms. The Court "
			"struck the section down entirely as unconstitutional under "
			"Article 19(1)(a) (freedom of speech and expression), holding its "
			"vagueness had a 'chilling effect' -- people would self-censor "
			"rather than risk prosecution under a standard nobody could "
			"predict. A landmark early ruling on free speech in the internet "
			"era, still the leading case cited against vague speech-restricting "
			"statutes."
		),
	},
	"minerva_mills_1980": {
		"case_name": "Minerva Mills v. Union of India",
		"year": 1980,
		"court": "Supreme Court of India",
		"related_articles": ["368", "31C"],
	},
	"puttaswamy_2017": {
		"case_name": "K.S. Puttaswamy v. Union of India",
		"year": 2017,
		"court": "Supreme Court of India",
		"related_articles": ["21"],
		"note": "Right to privacy",
	},
	"adr_v_election_commission_2024": {
		"case_name": "Association for Democratic Reforms v. Union of India",
		"year": 2024,
		"court": "Supreme Court of India",
		"citation": "2024 INSC 113",
		"related_articles": ["19"],
		"note": "Electoral bonds case",
	},
	"state_of_punjab_v_davinder_singh_2024": {
		"case_name": "State of Punjab v. Davinder Singh",
		"year": 2024,
		"court": "Supreme Court of India",
		"citation": "2024 INSC 562",
		"related_articles": ["341", "342", "15", "16"],
		"note": "SC/ST sub-classification",
	},
	"property_owners_association_2024": {
		"case_name": "Property Owners Association v. State of Maharashtra",
		"year": 2024,
		"court": "Supreme Court of India",
		"citation": "2024 INSC 835",
		"related_articles": ["39", "31C"],
	},
	"pooja_ramesh_singh_v_jk_bank_2026": {
		"case_name": "Pooja Ramesh Singh v. Jammu and Kashmir Bank Ltd. & Anr.",
		"year": 2026,
		"court": "Supreme Court of India",
		"citation": "2026 INSC 668",
		"related_articles": [],
		"note": "AI hallucinated precedents ruling. Left empty as it is not a fundamental rights case.",
	},
}

# Cases identified for future ingestion. NOT yet indexed — do not move an
# entry into CASE_METADATA above until scripts/index.py has confirmed it's
# actually live in Pinecone.
#
# The 4 entries below are blocked on re-sourcing: the PDFs dropped into
# data/raw/case_law/ for these were the WRONG document (verified by reading
# the extracted text's own header/citation against the expected case) —
# see ingestion.md. Their extracted (wrong) text was moved to
# data/processed/case_law/_wrong_source/ so it can never be picked up by
# scripts/chunk_case_law.py. Do NOT re-extract/chunk/index until the correct
# source PDF replaces the current file.
PENDING_CASE_METADATA = {
	"kesavananda_bharati_1973": {
		"case_name": "Kesavananda Bharati v. State of Kerala",
		"year": 1973,
		"court": "Supreme Court of India",
		"related_articles": ["368", "13", "19", "31"],
		"note": (
			"Basic structure doctrine. BLOCKED: data/raw/case_law/"
			"kesavananda_bharati_1973.pdf is the wrong document (contains "
			"Maharao Sahib Shri Bhim Singhji v. Union of India, 1980) — "
			"needs the correct source PDF."
		),
	},
	"golaknath_1967": {
		"case_name": "I.C. Golaknath v. State of Punjab",
		"year": 1967,
		"court": "Supreme Court of India",
		"related_articles": ["368", "13"],
		"note": (
			"BLOCKED: data/raw/case_law/golaknath_1967.pdf is the wrong "
			"document (contains Assam Sanmilita Mahasangha v. Union of "
			"India, 2014) — needs the correct source PDF."
		),
	},
	"sr_bommai_1994": {
		"case_name": "S.R. Bommai v. Union of India",
		"year": 1994,
		"court": "Supreme Court of India",
		"related_articles": ["356"],
		"note": (
			"BLOCKED: data/raw/case_law/sr_bommai_1994.pdf is the wrong "
			"document (contains a 2008 Kerala HC sales-tax writ order, ~1.5KB "
			"of text) — needs the correct source PDF."
		),
	},
	"in_re_article_370_2023": {
		"case_name": "In Re: Article 370 of the Constitution",
		"year": 2023,
		"court": "Supreme Court of India",
		"related_articles": ["370", "356"],
		"note": (
			"BLOCKED: data/raw/case_law/in_re_article_370_2023.pdf is only a "
			"procedural 'Record of Proceedings' from an Aug 8, 2023 hearing, "
			"not the final substantive judgment delivered Dec 11, 2023 — "
			"needs the correct source PDF."
		),
	},
}
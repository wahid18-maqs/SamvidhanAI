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
		"case_citation": "AIR 1978 SC 597",
		"date": 1978,
		"year": 1978,
		"court": "Supreme Court of India",
		"document_type": "case_law",
		"source_file": "maneka_gandhi_1978.pdf",
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
		"case_citation": "(2015) 5 SCC 1",
		"date": 2015,
		"year": 2015,
		"court": "Supreme Court of India",
		"document_type": "case_law",
		"source_file": "shreya_singhal_2015.pdf",
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
		"case_citation": "(1980) 3 SCC 625",
		"date": 1980,
		"year": 1980,
		"court": "Supreme Court of India",
		"document_type": "case_law",
		"source_file": "minerva_mills_1980.pdf",
		"related_articles": ["368", "31C"],
	},
	"puttaswamy_2017": {
		"case_name": "K.S. Puttaswamy v. Union of India",
		"case_citation": "(2017) 10 SCC 1",
		"date": 2017,
		"year": 2017,
		"court": "Supreme Court of India",
		"document_type": "case_law",
		"source_file": "puttaswamy_2017.pdf",
		"related_articles": ["21"],
		"note": "Right to privacy",
	},
	"adr_v_election_commission_2024": {
		"case_name": "Association for Democratic Reforms v. Union of India",
		"case_citation": "2024 INSC 113",
		"date": 2024,
		"year": 2024,
		"court": "Supreme Court of India",
		"document_type": "case_law",
		"source_file": "adr_v_election_commission_2024.pdf",
		"related_articles": ["19"],
		"note": "Electoral bonds case",
	},
	"state_of_punjab_v_davinder_singh_2024": {
		"case_name": "State of Punjab v. Davinder Singh",
		"case_citation": "2024 INSC 562",
		"date": 2024,
		"year": 2024,
		"court": "Supreme Court of India",
		"document_type": "case_law",
		"source_file": "state_of_punjab_v_davinder_singh_2024.pdf",
		"related_articles": ["341", "342", "15", "16"],
		"note": "SC/ST sub-classification",
	},
	"property_owners_association_2024": {
		"case_name": "Property Owners Association v. State of Maharashtra",
		"case_citation": "2024 INSC 835",
		"date": 2024,
		"year": 2024,
		"court": "Supreme Court of India",
		"document_type": "case_law",
		"source_file": "property_owners_association_2024.pdf",
		"related_articles": ["39", "31C"],
	},
	"pooja_ramesh_singh_v_jk_bank_2026": {
		"case_name": "Pooja Ramesh Singh v. Jammu and Kashmir Bank Ltd. & Anr.",
		"case_citation": "2026 INSC 668",
		"date": 2026,
		"year": 2026,
		"court": "Supreme Court of India",
		"document_type": "case_law",
		"source_file": "pooja_ramesh_singh_v_jk_bank_2026.pdf",
		"related_articles": [],
		"note": "AI hallucinated precedents ruling. Left empty as it is not a fundamental rights case.",
	},
	"golaknath_1967": {
		"case_name": "I.C. Golaknath v. State of Punjab",
		"case_citation": "1967 AIR 1643",
		"date": 1967,
		"year": 1967,
		"court": "Supreme Court of India",
		"document_type": "case_law",
		"source_file": "golaknath_1967.pdf",
		"related_articles": ["368", "13"],
	},
	"kesavananda_bharati_1973": {
		"case_name": "Kesavananda Bharati v. State of Kerala",
		"case_citation": "(1973) 4 SCC 225",
		"date": 1973,
		"year": 1973,
		"court": "Supreme Court of India",
		"document_type": "case_law",
		"source_file": "kesavananda_bharati_1973.pdf",
		"related_articles": ["368", "13", "19", "31"],
		"note": "Basic structure doctrine",
	},
	"sr_bommai_1994": {
		"case_name": "S.R. Bommai v. Union of India",
		"case_citation": "(1994) 3 SCC 1",
		"date": 1994,
		"year": 1994,
		"court": "Supreme Court of India",
		"document_type": "case_law",
		"source_file": "sr_bommai_1994.pdf",
		"related_articles": ["356"],
	},
	"in_re_article_370_2023": {
		"case_name": "In Re: Article 370 of the Constitution",
		"case_citation": "2023 INSC 1058",
		"date": 2023,
		"year": 2023,
		"court": "Supreme Court of India",
		"document_type": "case_law",
		"source_file": "in_re_article_370_2023.pdf",
		"related_articles": ["370", "356"],
	},
}

# Cases identified for future ingestion. NOT yet indexed — do not move an
# entry into CASE_METADATA above until scripts/index.py has confirmed it's
# actually live in Pinecone.
PENDING_CASE_METADATA = {}

# Alias fragments used to resolve a query to one specific case_id, so a
# case-law query can be narrowed to that one case's vectors instead of
# searching the whole case-law corpus by embedding similarity alone (see
# ingestion.md's retrieval-routing note -- that gap let a large judgment
# on the same doctrine crowd a smaller one out of the top-K results, e.g.
# Kesavananda Bharati crowding out Golaknath, which it discusses at
# length while overturning it).
#
# Deliberately more specific than a bare petitioner/respondent surname
# where that would collide with another case's party (e.g. "State of
# Punjab" is Golaknath's respondent too, so it's left out here even
# though it's fine as a broad classify_intent() signal). Bare "article
# 370" is left out for the same reason -- it's inherently ambiguous with
# a query about the constitutional provision itself -- so a query needs
# a case-flavored qualifier ("... case", "... judgment", "in re article
# 370", ...) to resolve to in_re_article_370_2023.
CASE_NAME_ALIASES: dict[str, list[str]] = {
	"maneka_gandhi_1978": ["maneka gandhi"],
	"shreya_singhal_2015": ["shreya singhal"],
	"minerva_mills_1980": ["minerva mills"],
	"puttaswamy_2017": ["puttaswamy"],
	"adr_v_election_commission_2024": ["association for democratic reforms"],
	"state_of_punjab_v_davinder_singh_2024": ["davinder singh"],
	"property_owners_association_2024": ["property owners association"],
	"pooja_ramesh_singh_v_jk_bank_2026": ["pooja ramesh singh"],
	"golaknath_1967": ["golaknath", "golak nath"],
	"kesavananda_bharati_1973": ["kesavananda bharati", "kesavananda"],
	"sr_bommai_1994": ["s.r. bommai", "sr bommai", "s. r. bommai", "bommai"],
	"in_re_article_370_2023": [
		"in re article 370",
		"in re: article 370",
		"article 370 case",
		"article 370 judgment",
		"article 370 judgement",
		"article 370 verdict",
		"article 370 ruling",
	],
}

REQUIRED_CASE_METADATA_FIELDS = (
	"case_name",
	"case_citation",
	"date",
	"court",
	"document_type",
	"source_file",
)


def validate_case_metadata(case_id: str, metadata: dict) -> list[str]:
	"""Return missing or inconsistent fields before a case is indexed."""
	issues = [
		field
		for field in REQUIRED_CASE_METADATA_FIELDS
		if metadata.get(field) in (None, "")
	]
	if metadata.get("document_type") != "case_law":
		issues.append("document_type must be 'case_law'")
	if metadata.get("year") != metadata.get("date"):
		issues.append("year must match date")
	source_file = metadata.get("source_file")
	if source_file and not source_file.endswith((".pdf", ".txt")):
		issues.append("source_file must be a .pdf or .txt path")
	if source_file and source_file.rsplit("/", 1)[-1].rsplit(".", 1)[0] != case_id:
		issues.append("source_file does not match case_id")
	return [f"{case_id}: {issue}" for issue in issues]


def resolve_case_ids(query: str) -> set[str]:
	"""Return every known case_id whose alias appears in the query text."""
	lowered = query.lower()
	return {
		case_id
		for case_id, aliases in CASE_NAME_ALIASES.items()
		if any(alias in lowered for alias in aliases)
	}


def resolve_single_case_id(query: str) -> str | None:
	"""Return the one case_id a query's aliases identify.

	None when zero aliases match (no case identified) or more than one
	case's aliases match (query names multiple cases, or is otherwise not
	confidently about a single one) -- both cases should fall back to
	searching the whole case-law corpus rather than force a wrong filter.
	"""
	matches = resolve_case_ids(query)
	if len(matches) == 1:
		return next(iter(matches))
	return None
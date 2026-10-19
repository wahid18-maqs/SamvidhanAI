"""Unit tests for case-law chunking and metadata extraction."""

import unittest

from scripts.chunk_case_law import (
	_metadata_for_chunk,
	case_metadata_for,
	chunk_case_text,
	split_by_paragraph_number,
)


class CaseLawParagraphSplitTests(unittest.TestCase):
	def test_splits_on_numbered_paragraphs(self):
		text = (
			"12. This is the first holding paragraph.\n"
			"13. This is the second holding paragraph, continuing\n"
			"across a line wrap.\n"
			"14. This is the third."
		)
		paragraphs = split_by_paragraph_number(text)
		self.assertEqual(len(paragraphs), 3)
		self.assertTrue(paragraphs[0].startswith("12."))
		self.assertTrue(paragraphs[1].startswith("13."))
		self.assertIn("continuing", paragraphs[1])
		self.assertTrue(paragraphs[2].startswith("14."))

	def test_no_split_when_too_few_numbered_paragraphs(self):
		text = "1. Only one numbered line in an otherwise unnumbered judgment scan."
		self.assertEqual(split_by_paragraph_number(text), [])

	def test_no_split_when_a_headnote_number_swallows_unnumbered_prose(self):
		# Mimics an old scan where only a short headnote is numbered and the
		# rest of the opinion runs on as unnumbered prose.
		text = (
			"4. Headnote point one.\n"
			"6. Headnote point two.\n"
			"14. Headnote point three.\n" + ("Unnumbered prose. " * 1000)
		)
		self.assertEqual(split_by_paragraph_number(text), [])

	def test_chunk_case_text_falls_back_to_fixed_windows(self):
		text = "A" * 2500
		chunks = chunk_case_text(text)
		self.assertGreater(len(chunks), 1)
		self.assertTrue(all(chunk for chunk in chunks))

	def test_chunk_case_text_prefers_paragraph_split(self):
		text = "1. First.\n2. Second.\n3. Third.\n4. Fourth."
		chunks = chunk_case_text(text)
		self.assertEqual(len(chunks), 4)


class CaseLawMetadataTests(unittest.TestCase):
	def test_known_case_metadata_shape(self):
		metadata = _metadata_for_chunk("maneka_gandhi_1978", 0)
		self.assertEqual(metadata["case_id"], "maneka_gandhi_1978")
		self.assertEqual(metadata["case_name"], "Maneka Gandhi v. Union of India")
		self.assertEqual(metadata["case_citation"], "AIR 1978 SC 597")
		self.assertEqual(metadata["date"], 1978)
		self.assertEqual(metadata["year"], 1978)
		self.assertEqual(metadata["document_type"], "case_law")
		self.assertEqual(metadata["category"], "constitutional_law")
		self.assertEqual(metadata["source_file"], "maneka_gandhi_1978.pdf")
		self.assertFalse(metadata["metadata_extraction_failed"])

	def test_unregistered_case_id_is_flagged(self):
		metadata = _metadata_for_chunk("some_unregistered_case", 0)
		self.assertIsNone(metadata["case_name"])
		self.assertTrue(metadata["metadata_extraction_failed"])
		self.assertTrue(
			any("no case metadata registered" in warning for warning in metadata["metadata_warnings"])
		)

	def test_case_metadata_for_unknown_slug_returns_placeholder(self):
		info = case_metadata_for("unknown_case_2099")
		self.assertIsNone(info["case_name"])
		self.assertIsNone(info["year"])
		self.assertIsNone(info["court"])


if __name__ == "__main__":
	unittest.main()

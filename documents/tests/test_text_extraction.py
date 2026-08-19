import os
import tempfile

from django.test import SimpleTestCase

from documents.utils.text_extraction import (
    TextExtractionError,
    count_words,
    extract_text,
)


class TextExtractionTests(SimpleTestCase):
    def test_extract_txt(self):
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", delete=False
        ) as f:
            f.write("Hello world, this is a test document.")
            path = f.name
        try:
            text = extract_text(path, ".txt")
            self.assertIn("Hello world", text)
        finally:
            os.remove(path)

    def test_extract_empty_txt_raises(self):
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", delete=False
        ) as f:
            f.write("   ")
            path = f.name
        try:
            with self.assertRaises(TextExtractionError):
                extract_text(path, ".txt")
        finally:
            os.remove(path)

    def test_unsupported_extension_raises(self):
        with tempfile.NamedTemporaryFile(
            suffix=".xyz", mode="w", delete=False
        ) as f:
            f.write("content")
            path = f.name
        try:
            with self.assertRaises(TextExtractionError):
                extract_text(path, ".xyz")
        finally:
            os.remove(path)

    def test_count_words(self):
        self.assertEqual(count_words("one two three"), 3)
        self.assertEqual(count_words(""), 0)
        self.assertEqual(count_words(None), 0)

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from documents.models import Document


class DocumentModelTests(TestCase):
    def test_document_created_with_defaults(self):
        doc = Document.objects.create(
            file=SimpleUploadedFile("sample.txt", b"hello world"),
            original_filename="sample.txt",
            file_type=".txt",
            file_size=11,
        )
        self.assertEqual(doc.status, Document.Status.PENDING)
        self.assertEqual(doc.word_count, 0)
        self.assertEqual(doc.llm_keywords, [])
        self.assertIsNotNone(doc.id)

    def test_str_representation(self):
        doc = Document.objects.create(
            file=SimpleUploadedFile("sample.txt", b"hello world"),
            original_filename="sample.txt",
            file_type=".txt",
            file_size=11,
        )
        self.assertIn("sample.txt", str(doc))
        self.assertIn("pending", str(doc))

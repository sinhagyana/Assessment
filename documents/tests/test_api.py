from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from documents.models import Document


class DocumentUploadAPITests(APITestCase):
    def test_upload_rejects_missing_file(self):
        url = reverse("document-upload")
        response = self.client.post(url, {}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_rejects_unsupported_extension(self):
        url = reverse("document-upload")
        bad_file = SimpleUploadedFile(
            "malware.exe", b"binary content", content_type="application/octet-stream"
        )
        response = self.client.post(url, {"file": bad_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_rejects_empty_file(self):
        url = reverse("document-upload")
        empty_file = SimpleUploadedFile("empty.txt", b"", content_type="text/plain")
        response = self.client.post(url, {"file": empty_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("documents.services.analyze_document")
    def test_upload_successful_processing(self, mock_analyze):
        mock_analyze.return_value = {
            "title": "Test Title",
            "summary": "Test summary.",
            "keywords": ["test", "document"],
            "language": "English",
            "word_count": 5,
            "raw_response": {"title": "Test Title"},
        }
        url = reverse("document-upload")
        txt_file = SimpleUploadedFile(
            "notes.txt", b"This is a simple test document.", content_type="text/plain"
        )
        response = self.client.post(url, {"file": txt_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Document.Status.COMPLETED)
        self.assertEqual(response.data["llm_title"], "Test Title")

    @patch("documents.services.analyze_document")
    def test_upload_marks_failed_on_llm_error(self, mock_analyze):
        from documents.utils.llm_service import LLMServiceError

        mock_analyze.side_effect = LLMServiceError("simulated failure")
        url = reverse("document-upload")
        txt_file = SimpleUploadedFile(
            "notes.txt", b"This is a simple test document.", content_type="text/plain"
        )
        response = self.client.post(url, {"file": txt_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["status"], Document.Status.FAILED)


class DocumentListDetailAPITests(APITestCase):
    def setUp(self):
        self.doc = Document.objects.create(
            file=SimpleUploadedFile("sample.txt", b"hello world"),
            original_filename="sample.txt",
            file_type=".txt",
            file_size=11,
            status=Document.Status.COMPLETED,
            llm_title="Sample Title",
        )

    def test_list_documents(self):
        url = reverse("document-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_status(self):
        url = reverse("document-list")
        response = self.client.get(url, {"status": "failed"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_retrieve_document_detail(self):
        url = reverse("document-detail", kwargs={"id": self.doc.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["llm_title"], "Sample Title")

    def test_retrieve_nonexistent_document_returns_404(self):
        import uuid

        url = reverse("document-detail", kwargs={"id": uuid.uuid4()})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

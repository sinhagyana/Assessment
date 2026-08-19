import logging
import os

from django.utils import timezone

from .models import Document
from .utils.llm_service import LLMServiceError, analyze_document
from .utils.text_extraction import TextExtractionError, count_words, extract_text

logger = logging.getLogger("documents")


def process_document(document: Document) -> Document:
    document.status = Document.Status.PROCESSING
    document.save(update_fields=["status", "updated_at"])

    try:
        file_path = document.file.path
        text = extract_text(file_path, document.file_type)
        document.extracted_text = text
        document.word_count = count_words(text)

        analysis = analyze_document(text)
        document.llm_title = analysis["title"]
        document.llm_summary = analysis["summary"]
        document.llm_keywords = analysis["keywords"]
        document.llm_language = analysis["language"]
        document.llm_raw_response = analysis.get("raw_response")

        document.status = Document.Status.COMPLETED
        document.error_message = ""
        document.processed_at = timezone.now()

    except TextExtractionError as exc:
        logger.warning("Text extraction failed for %s: %s", document.id, exc)
        document.status = Document.Status.FAILED
        document.error_message = f"Text extraction failed: {exc}"

    except LLMServiceError as exc:
        logger.warning("LLM analysis failed for %s: %s", document.id, exc)
        document.status = Document.Status.FAILED
        document.error_message = f"LLM analysis failed: {exc}"

    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error processing document %s", document.id)
        document.status = Document.Status.FAILED
        document.error_message = f"Unexpected error: {exc}"

    document.save()
    return document

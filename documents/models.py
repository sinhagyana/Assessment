import os
import uuid

from django.db import models


def upload_to(instance, filename):
    ext = os.path.splitext(filename)[1]
    new_name = f"{uuid.uuid4().hex}{ext}"
    return os.path.join("uploads", new_name)


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to=upload_to)
    file_type = models.CharField(max_length=10)
    file_size = models.PositiveIntegerField(help_text="Size in bytes")

    extracted_text = models.TextField(blank=True, default="")
    word_count = models.PositiveIntegerField(default=0)

    llm_title = models.CharField(max_length=500, blank=True, default="")
    llm_summary = models.TextField(blank=True, default="")
    llm_keywords = models.JSONField(blank=True, default=list)
    llm_language = models.CharField(max_length=50, blank=True, default="")
    llm_raw_response = models.JSONField(blank=True, null=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    error_message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.original_filename} ({self.status})"

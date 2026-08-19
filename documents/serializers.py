import os

from django.conf import settings
from rest_framework import serializers

from .models import Document


class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)

    class Meta:
        model = Document
        fields = ["id", "file", "original_filename", "status", "created_at"]
        read_only_fields = ["id", "original_filename", "status", "created_at"]

    def validate_file(self, value):
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type '{ext}'. Allowed types: "
                f"{', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}"
            )
        if value.size == 0:
            raise serializers.ValidationError("Uploaded file is empty.")
        if value.size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise serializers.ValidationError(
                f"File too large. Maximum allowed size is "
                f"{settings.MAX_UPLOAD_SIZE_MB} MB."
            )
        return value


class DocumentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "original_filename",
            "file_type",
            "file_size",
            "status",
            "llm_title",
            "word_count",
            "created_at",
            "updated_at",
        ]


class DocumentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "original_filename",
            "file",
            "file_type",
            "file_size",
            "extracted_text",
            "word_count",
            "llm_title",
            "llm_summary",
            "llm_keywords",
            "llm_language",
            "status",
            "error_message",
            "created_at",
            "updated_at",
            "processed_at",
        ]

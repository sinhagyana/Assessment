from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "original_filename",
        "file_type",
        "status",
        "word_count",
        "created_at",
    )
    list_filter = ("status", "file_type")
    search_fields = ("original_filename", "llm_title")
    readonly_fields = ("id", "created_at", "updated_at", "processed_at")

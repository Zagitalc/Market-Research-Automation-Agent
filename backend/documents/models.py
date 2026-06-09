from django.db import models
from django.utils import timezone


def document_upload_path(instance, filename: str) -> str:
    uploaded_at = instance.created_at or timezone.now()
    return f"documents/{uploaded_at:%Y/%m/%d}/{filename}"


class Document(models.Model):
    class IngestionStatus(models.TextChoices):
        COMPLETED = "completed", "Completed"

    title = models.CharField(max_length=255)
    source_type = models.CharField(max_length=100)
    content = models.TextField()
    original_filename = models.CharField(max_length=255, blank=True, default="")
    file_type = models.CharField(max_length=20, blank=True, default="")
    file_size = models.PositiveBigIntegerField(blank=True, null=True)
    source_file = models.FileField(upload_to=document_upload_path, blank=True, null=True)
    ingestion_status = models.CharField(
        max_length=20,
        choices=IngestionStatus.choices,
        default=IngestionStatus.COMPLETED,
    )
    ingestion_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class DocumentChunk(models.Model):
    document = models.ForeignKey(Document, related_name="chunks", on_delete=models.CASCADE)
    chunk_text = models.TextField()
    embedding = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"Chunk {self.id} for {self.document_id}"

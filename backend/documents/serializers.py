from rest_framework import serializers

from documents.models import Document, DocumentChunk
from documents.services.chunker import create_chunks_for_document
from documents.services.ingestion import create_document_from_upload


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = ["id", "document", "chunk_text", "embedding", "created_at"]
        read_only_fields = ["id", "created_at"]


class DocumentSerializer(serializers.ModelSerializer):
    chunks = DocumentChunkSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "source_type",
            "content",
            "original_filename",
            "file_type",
            "file_size",
            "ingestion_status",
            "ingestion_error",
            "created_at",
            "updated_at",
            "chunks",
        ]
        read_only_fields = [
            "id",
            "original_filename",
            "file_type",
            "file_size",
            "ingestion_status",
            "ingestion_error",
            "created_at",
            "updated_at",
            "chunks",
        ]

    def create(self, validated_data):
        document = super().create(validated_data)
        create_chunks_for_document(document)
        return document


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def create(self, validated_data):
        return create_document_from_upload(
            uploaded_file=validated_data["file"],
            title=validated_data.get("title", ""),
        )

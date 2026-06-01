from rest_framework import serializers

from documents.models import Document, DocumentChunk


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = ["id", "document", "chunk_text", "embedding", "created_at"]
        read_only_fields = ["id", "created_at"]


class DocumentSerializer(serializers.ModelSerializer):
    chunks = DocumentChunkSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ["id", "title", "source_type", "content", "created_at", "updated_at", "chunks"]
        read_only_fields = ["id", "created_at", "updated_at", "chunks"]

    def create(self, validated_data):
        document = super().create(validated_data)
        DocumentChunk.objects.create(
            document=document,
            chunk_text=document.content[:1200],
            embedding=[],
        )
        return document

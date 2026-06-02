import pytest
from django.core.management import call_command

from documents.models import Document, DocumentChunk


@pytest.mark.django_db
def test_backfill_dry_run_does_not_update_empty_embedding():
    document = Document.objects.create(title="Backfill doc", source_type="note", content="Needs embedding")
    chunk = DocumentChunk.objects.create(document=document, chunk_text="Needs embedding", embedding=[])

    call_command("backfill_chunk_embeddings", "--dry-run")

    chunk.refresh_from_db()
    assert chunk.embedding == []


@pytest.mark.django_db
def test_backfill_regenerates_empty_embedding():
    document = Document.objects.create(title="Backfill doc", source_type="note", content="Needs embedding")
    chunk = DocumentChunk.objects.create(document=document, chunk_text="Needs embedding", embedding=[])

    call_command("backfill_chunk_embeddings")

    chunk.refresh_from_db()
    assert chunk.embedding

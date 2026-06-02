from django.core.management.base import BaseCommand

from agents.services.embedding_provider import generate_embedding, get_ai_mode
from documents.models import DocumentChunk


class Command(BaseCommand):
    help = "Regenerate embeddings for DocumentChunk rows with empty embeddings."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report chunks that would be updated.")
        parser.add_argument("--all", action="store_true", help="Regenerate all chunk embeddings, not only empty ones.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        regenerate_all = options["all"]
        queryset = DocumentChunk.objects.all() if regenerate_all else DocumentChunk.objects.filter(embedding=[])
        count = queryset.count()

        if dry_run:
            self.stdout.write(f"{count} chunk embedding(s) would be regenerated in {get_ai_mode()} mode.")
            return

        updated = 0
        for chunk in queryset.iterator():
            chunk.embedding = generate_embedding(chunk.chunk_text)
            chunk.save(update_fields=["embedding"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Regenerated {updated} chunk embedding(s) in {get_ai_mode()} mode."))

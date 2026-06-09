from django.db.models.signals import post_delete
from django.dispatch import receiver

from documents.models import Document


@receiver(post_delete, sender=Document)
def delete_document_source_file(sender, instance: Document, **kwargs) -> None:
    if instance.source_file:
        instance.source_file.delete(save=False)

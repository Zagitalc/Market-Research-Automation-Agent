from rest_framework import mixins, viewsets

from documents.models import Document
from documents.serializers import DocumentSerializer


class DocumentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Document.objects.prefetch_related("chunks").all()
    serializer_class = DocumentSerializer

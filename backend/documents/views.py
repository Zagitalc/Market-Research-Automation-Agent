from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from documents.models import Document
from documents.serializers import DocumentSerializer


class DocumentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Document.objects.prefetch_related("chunks").all()
    serializer_class = DocumentSerializer

    @action(detail=False, methods=["delete"])
    def clear(self, request):
        document_count = Document.objects.count()
        deleted_count, deleted_details = Document.objects.all().delete()
        return Response(
            {
                "deleted": document_count,
                "deleted_rows": deleted_count,
                "details": deleted_details,
            }
        )

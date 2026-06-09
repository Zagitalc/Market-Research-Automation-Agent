from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from config.throttles import ConfiguredScopedRateThrottle
from documents.models import Document
from documents.serializers import DocumentSerializer, DocumentUploadSerializer


class DocumentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Document.objects.prefetch_related("chunks").all()
    serializer_class = DocumentSerializer

    def get_throttles(self):
        throttles = super().get_throttles()
        if self.action in {"create", "upload"}:
            self.throttle_scope = "document_create"
            throttles.append(ConfiguredScopedRateThrottle())
        return throttles

    @action(
        detail=False,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        return Response(
            DocumentSerializer(document, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

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

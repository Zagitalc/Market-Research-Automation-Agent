from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.views import DocumentViewSet
from research.views import ResearchRunViewSet


class HealthCheckView(APIView):
    def get(self, request):
        return Response({"status": "ok"})


router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="document")
router.register("research-runs", ResearchRunViewSet, basename="research-run")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthCheckView.as_view(), name="health"),
    path("api/", include(router.urls)),
]

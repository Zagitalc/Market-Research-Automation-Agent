from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from agents.serializers import AgentStepSerializer
from agents.services.agent_runner import run_research_agent
from config.throttles import ConfiguredScopedRateThrottle
from research.models import ResearchRun
from research.serializers import ResearchRunSerializer


class ResearchRunViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ResearchRun.objects.prefetch_related("steps").all()
    serializer_class = ResearchRunSerializer

    def get_throttles(self):
        throttles = super().get_throttles()
        if self.action == "create":
            self.throttle_scope = "research_run_create"
            throttles.append(ConfiguredScopedRateThrottle())
        return throttles

    def perform_create(self, serializer):
        research_run = serializer.save(status=ResearchRun.Status.RUNNING)
        run_research_agent(research_run)

    @action(detail=True, methods=["get"])
    def steps(self, request, pk=None):
        research_run = self.get_object()
        serializer = AgentStepSerializer(research_run.steps.all(), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["delete"])
    def clear(self, request):
        run_count = ResearchRun.objects.count()
        deleted_count, deleted_details = ResearchRun.objects.all().delete()
        return Response(
            {
                "deleted": run_count,
                "deleted_rows": deleted_count,
                "details": deleted_details,
            }
        )

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from agents.serializers import AgentStepSerializer
from agents.services.agent_runner import run_research_agent
from research.models import ResearchRun
from research.serializers import ResearchRunSerializer


class ResearchRunViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ResearchRun.objects.prefetch_related("steps").all()
    serializer_class = ResearchRunSerializer

    def perform_create(self, serializer):
        research_run = serializer.save(status=ResearchRun.Status.RUNNING)
        run_research_agent(research_run)

    @action(detail=True, methods=["get"])
    def steps(self, request, pk=None):
        research_run = self.get_object()
        serializer = AgentStepSerializer(research_run.steps.all(), many=True)
        return Response(serializer.data)

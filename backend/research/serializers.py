from rest_framework import serializers

from agents.serializers import AgentStepSerializer
from research.models import ResearchRun


class ResearchRunSerializer(serializers.ModelSerializer):
    steps = AgentStepSerializer(many=True, read_only=True)

    class Meta:
        model = ResearchRun
        fields = [
            "id",
            "user_query",
            "status",
            "final_answer",
            "confidence_score",
            "created_at",
            "updated_at",
            "steps",
        ]
        read_only_fields = [
            "id",
            "status",
            "final_answer",
            "confidence_score",
            "created_at",
            "updated_at",
            "steps",
        ]

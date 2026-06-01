from rest_framework import serializers

from agents.models import AgentStep


class AgentStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentStep
        fields = ["id", "research_run", "step_type", "input_data", "output_data", "created_at"]
        read_only_fields = ["id", "research_run", "created_at"]

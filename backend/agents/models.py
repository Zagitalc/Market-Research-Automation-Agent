from django.db import models


class AgentStep(models.Model):
    class StepType(models.TextChoices):
        PLAN = "plan", "Plan"
        RETRIEVE = "retrieve", "Retrieve"
        TOOL_CALL = "tool_call", "Tool Call"
        REFLECT = "reflect", "Reflect"
        FINAL = "final", "Final"

    research_run = models.ForeignKey("research.ResearchRun", related_name="steps", on_delete=models.CASCADE)
    step_type = models.CharField(max_length=20, choices=StepType.choices)
    input_data = models.JSONField(default=dict, blank=True)
    output_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return f"{self.step_type} for run {self.research_run_id}"

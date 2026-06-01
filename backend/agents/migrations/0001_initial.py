from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("research", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AgentStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "step_type",
                    models.CharField(
                        choices=[
                            ("plan", "Plan"),
                            ("retrieve", "Retrieve"),
                            ("tool_call", "Tool Call"),
                            ("reflect", "Reflect"),
                            ("final", "Final"),
                        ],
                        max_length=20,
                    ),
                ),
                ("input_data", models.JSONField(blank=True, default=dict)),
                ("output_data", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "research_run",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="steps", to="research.researchrun"),
                ),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
    ]

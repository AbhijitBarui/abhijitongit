from django.db import models
from django.utils import timezone

class TaskGroup(models.Model):
    name = models.CharField(max_length=120, unique=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Task(models.Model):
    DESIRED_CHOICES = [
        ("early_morning","Early morning"),
        ("morning","Morning"),
        ("afternoon","Afternoon"),
        ("evening","Evening"),
        ("night","Night"),
        ("any","Any"),
    ]
    title = models.CharField(max_length=160)
    group = models.ForeignKey(TaskGroup, on_delete=models.CASCADE, related_name="tasks")
    duration_min = models.PositiveIntegerField(default=30)
    priority = models.IntegerField(default=3)  # 1–5
    desired_time = models.CharField(max_length=20, choices=DESIRED_CHOICES, default="any")
    deadline = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class DayPlan(models.Model):
    date = models.DateField(default=timezone.localdate, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Plan {self.date}"

class PlanItem(models.Model):
    plan = models.ForeignKey(DayPlan, on_delete=models.CASCADE, related_name="items")
    task = models.ForeignKey(Task, on_delete=models.PROTECT)
    group_name = models.CharField(max_length=120)  # denormalized for display
    start_hhmm = models.CharField(max_length=5)    # "09:00"
    end_hhmm = models.CharField(max_length=5)
    done = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["start_hhmm", "order"]

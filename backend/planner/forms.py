from django import forms
from .models import Task, TaskGroup

# class TaskForm(forms.ModelForm):
#     class Meta:
#         model = Task
#         fields = ["title", "group", "duration_min", "priority", "desired_time", "deadline", "active"]



class TaskForm(forms.ModelForm):
    deadline_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    class Meta:
        model = Task
        fields = [
            "title","group","duration_min","priority","desired_time","active",
            "recurrence","recur_interval","recur_weekdays","recur_monthday",
            "start_date","end_date","deadline_at"  # <- add here
        ]

class TaskGroupForm(forms.ModelForm):
    class Meta:
        model = TaskGroup
        fields = ["name", "notes"]

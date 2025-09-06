from django import forms
from .models import Task, TaskGroup

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "group", "duration_min", "priority", "desired_time", "deadline", "active"]

class TaskGroupForm(forms.ModelForm):
    class Meta:
        model = TaskGroup
        fields = ["name", "notes"]

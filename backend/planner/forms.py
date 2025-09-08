from django import forms
from .models import Task, TaskGroup

# class TaskForm(forms.ModelForm):
#     class Meta:
#         model = Task
#         fields = ["title", "group", "duration_min", "priority", "desired_time", "deadline", "active"]



class TaskForm(forms.ModelForm):
    description_text = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Notes…"})
    )
    class Meta:
        model = Task
        fields = [
            "title","group","duration_min","priority","desired_time","active",
            "recurrence","recur_interval","recur_weekdays","recur_monthday",
            "start_date","end_date",
            "deadline_at",              # if you added this earlier
            "description_type","description_text"
        ]

class TaskGroupForm(forms.ModelForm):
    class Meta:
        model = TaskGroup
        fields = ["name", "notes"]

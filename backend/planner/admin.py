from django.contrib import admin
from .models import Task, TaskGroup, DayPlan, PlanItem

@admin.register(TaskGroup)
class TaskGroupAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title","group","duration_min","priority","desired_time","deadline","active")
    list_filter = ("group","desired_time","active")
    search_fields = ("title",)

class PlanItemInline(admin.TabularInline):
    model = PlanItem
    extra = 0

@admin.register(DayPlan)
class DayPlanAdmin(admin.ModelAdmin):
    list_display = ("date","created_at")
    inlines = [PlanItemInline]

import json
from datetime import date as dtdate
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from .models import DayPlan, PlanItem, Task, TaskGroup
from .forms import TaskForm, TaskGroupForm

def _today():
    return timezone.localdate()

@require_http_methods(["GET"])
def agenda_today(request):
    d = _today()
    plan = DayPlan.objects.filter(date=d).first()
    items = plan.items.select_related("task").all() if plan else []
    return render(request, "planner/agenda_today.html", {"date": d, "plan": plan, "items": items})

@require_http_methods(["GET", "POST"])
@transaction.atomic
def agenda_edit(request):
    d = _today()
    plan, _ = DayPlan.objects.get_or_create(date=d)

    if request.method == "POST":
        # Expect a single hidden field 'items_json' with a list of rows
        # [{"task_id": 3, "start": "09:00", "end": "10:00"}, ...]
        try:
            rows = json.loads(request.POST.get("items_json", "[]"))
        except Exception:
            return HttpResponseBadRequest("Bad items payload")

        plan.items.all().delete()
        bulk = []
        for idx, r in enumerate(rows):
            t = Task.objects.get(id=int(r["task_id"]))
            bulk.append(PlanItem(
                plan=plan,
                task=t,
                group_name=t.group.name,
                start_hhmm=r["start"],
                end_hhmm=r["end"],
                order=idx
            ))
        PlanItem.objects.bulk_create(bulk)
        return redirect("planner:agenda-today")

    # GET: show existing items + task list for the drawer
    tasks = Task.objects.filter(active=True).select_related("group").order_by("-priority", "duration_min")
    items = plan.items.select_related("task").all()
    groups = TaskGroup.objects.all().order_by("name")
    return render(request, "planner/agenda_edit.html", {
        "date": d, "items": items, "tasks": tasks, "groups": groups
    })

def add_entry(request):
    # simple chooser page
    return render(request, "planner/add_entry.html")

@require_http_methods(["GET", "POST"])
def add_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            # after adding a task, go back to /agenda/edit to place it
            return redirect("planner:agenda-edit")
    else:
        form = TaskForm()
    return render(request, "planner/add_task.html", {"form": form})

@require_http_methods(["GET", "POST"])
def add_group(request):
    if request.method == "POST":
        form = TaskGroupForm(request.POST)
        if form.is_valid():
            form.save()
            # after creating group, send to add task to use it (nice flow)
            return redirect("planner:add-task")
    else:
        form = TaskGroupForm()
    return render(request, "planner/add_group.html", {"form": form})

def manage_hub(request):
    return render(request, "planner/manage.html")

from django.shortcuts import get_object_or_404

@require_http_methods(["POST"])
def toggle_done(request, item_id):
    it = get_object_or_404(PlanItem, id=item_id)
    it.done = not it.done
    it.save(update_fields=["done"])
    return redirect("planner:agenda-today")


from django.forms import modelform_factory
from django.contrib import messages

# ----- TASKS -----
# def tasks_list(request):
#     qs = Task.objects.select_related("group").order_by("group__name","-priority","title")
#     return render(request, "planner/tasks_list.html", {"tasks": qs})
def tasks_list(request):
    qs = Task.objects.select_related("group").order_by("group__name","-priority","title")
    q = request.GET.get("q")
    if q:
        qs = qs.filter(title__icontains=q)
    return render(request, "planner/tasks_list.html", {"tasks": qs})


@require_http_methods(["GET","POST"])
def task_edit(request, pk):
    Form = modelform_factory(Task, fields=["title","group","duration_min","priority","desired_time","deadline","active"])
    obj = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        form = Form(request.POST, instance=obj)
        if form.is_valid():
            form.save(); messages.success(request,"Saved"); return redirect("planner:tasks-list")
    else:
        form = Form(instance=obj)
    return render(request, "planner/simple_form.html", {"form": form, "title": f"Edit Task: {obj.title}"})

@require_http_methods(["POST"])
def task_delete(request, pk):
    get_object_or_404(Task, pk=pk).delete()
    messages.success(request, "Deleted")
    return redirect("planner:tasks-list")

# from django.db.models.deletion import ProtectedError
# from django.contrib import messages
# from django.shortcuts import get_object_or_404, redirect
# from .models import Task, PlanItem

# @require_http_methods(["POST"])
# def task_delete(request, pk):
#     obj = get_object_or_404(Task, pk=pk)
#     try:
#         obj.delete()
#         messages.success(request, "Task deleted.")
#     except ProtectedError:
#         # Soft-delete when the task is referenced in any plan
#         cnt = PlanItem.objects.filter(task=obj).count()
#         obj.active = False
#         obj.save(update_fields=["active"])
#         messages.warning(
#             request,
#             f"Task is used in {cnt} agenda item(s); marked as inactive instead."
#         )
#     return redirect("planner:tasks-list")


# ----- GROUPS -----
def groups_list(request):
    qs = TaskGroup.objects.order_by("name")
    return render(request, "planner/groups_list.html", {"groups": qs})

@require_http_methods(["GET","POST"])
def group_edit(request, pk):
    Form = modelform_factory(TaskGroup, fields=["name","notes"])
    obj = get_object_or_404(TaskGroup, pk=pk)
    if request.method == "POST":
        form = Form(request.POST, instance=obj)
        if form.is_valid():
            form.save(); messages.success(request,"Saved"); return redirect("planner:groups-list")
    else:
        form = Form(instance=obj)
    return render(request, "planner/simple_form.html", {"form": form, "title": f"Edit Group: {obj.name}"})

@require_http_methods(["POST"])
def group_delete(request, pk):
    get_object_or_404(TaskGroup, pk=pk).delete()
    messages.success(request, "Deleted")
    return redirect("planner:groups-list")

# ----- AGENDAS -----
# def agendas_list(request):
#     qs = DayPlan.objects.order_by("-date").prefetch_related("items")
#     return render(request, "planner/agendas_list.html", {"plans": qs})

def agendas_list(request):
    plans = DayPlan.objects.order_by("-date").prefetch_related("items")
    rows = []
    for p in plans:
        total = p.items.count()
        done = p.items.filter(done=True).count()
        rows.append({"plan": p, "total": total, "done": done})
    return render(request, "planner/agendas_list.html", {"rows": rows})



@require_http_methods(["POST"])
def task_purge(request, pk):
    obj = get_object_or_404(Task, pk=pk)
    PlanItem.objects.filter(task=obj).delete()
    obj.delete()
    messages.success(request, "Task and its scheduled items were permanently deleted.")
    return redirect("planner:tasks-list")

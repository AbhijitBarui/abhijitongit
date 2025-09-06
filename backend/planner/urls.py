from django.urls import path
from . import views

app_name = "planner"

urlpatterns = [
    path("", views.agenda_today, name="agenda-today"),            # /agenda
    path("edit/", views.agenda_edit, name="agenda-edit"),         # /agenda/edit
    path("add/", views.add_entry, name="agenda-add"),             # /agenda/add (chooser)
    path("add/task/", views.add_task, name="add-task"),           # /agenda/add/task
    path("add/group/", views.add_group, name="add-group"),        # /agenda/add/group
    path("manage/", views.manage_hub, name="manage"),             # /agenda/manage\

    # toggle route
    path("item/<int:item_id>/toggle-done/", views.toggle_done, name="toggle-done"),

    # Manage hub is already there
    path("manage/tasks/", views.tasks_list, name="tasks-list"),
    path("manage/tasks/<int:pk>/edit/", views.task_edit, name="task-edit"),
    path("manage/tasks/<int:pk>/delete/", views.task_delete, name="task-delete"),

    path("manage/groups/", views.groups_list, name="groups-list"),
    path("manage/groups/<int:pk>/edit/", views.group_edit, name="group-edit"),
    path("manage/groups/<int:pk>/delete/", views.group_delete, name="group-delete"),

    path("manage/agendas/", views.agendas_list, name="agendas-list"),


]

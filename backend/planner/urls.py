from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "planner"

urlpatterns = [

    path("login/",  auth_views.LoginView.as_view(template_name="planner/agenda_login.html"), name="agenda-login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="agenda-logout"),

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

    path("manage/tasks/<int:pk>/purge/", views.task_purge, name="task-purge"),

    path("item/<int:item_id>/delay/", views.delay_after, name="delay-after"),



    # Checklist operations (AJAX-friendly)
    path("task/<int:task_id>/check/add/",    views.check_add,    name="check-add"),
    path("task/<int:task_id>/check/toggle/<int:item_id>/", views.check_toggle, name="check-toggle"),
    path("task/<int:task_id>/check/delete/<int:item_id>/", views.check_delete, name="check-delete"),

    path("task/<int:task_id>/drawing/save/", views.drawing_save, name="drawing-save"),
    path("drawing/<int:pk>/delete/",        views.drawing_delete, name="drawing-delete"),

    # Attachments
    path("task/<int:task_id>/attach/upload/",  views.attach_upload, name="attach-upload"),
    path("attach/<int:pk>/delete/",            views.attach_delete, name="attach-delete"),

]

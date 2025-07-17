from django.urls import path
from . import views

urlpatterns = [
    path('projects/', views.ProjectListView.as_view(), name='project-list'),
    path('skills/', views.SkillListView.as_view(), name='skill-list'),
    path('experience/', views.ExperienceListView.as_view(), name='experience-list'),
    path('contact/', views.ContactCreateView.as_view(), name='contact-create'),
]

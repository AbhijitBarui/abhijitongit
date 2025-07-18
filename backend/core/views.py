from django.shortcuts import render
from rest_framework import generics
from .models import Project, Skill, Experience, ContactMessage
from .serializers import ProjectSerializer, SkillSerializer, ExperienceSerializer, ContactMessageSerializer
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import now


# HTML PAGES
def home_view(request):
    return render(request, 'core/home.html', {'now': now()})

def projects_view(request):
    return render(request, 'core/projects.html')

def contact_view(request):
    return render(request, 'core/contact.html')


# API Views
class ProjectListView(generics.ListAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

class SkillListView(generics.ListAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer

class ExperienceListView(generics.ListAPIView):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer

class ContactCreateView(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        send_mail(
            subject=f"Portfolio Contact from {instance.name}",
            message=instance.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_RECEIVER_EMAIL],
            fail_silently=True,
        )

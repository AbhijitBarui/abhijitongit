from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Core HTML pages (home, projects, contact)
    path('', include('core.urls')),  # loads views like '/', '/projects/', etc.
    
    # APIs under separate namespace
    path('api/', include(('core.api_urls', 'core'), namespace='core-api')),
]

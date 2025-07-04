"""
Project URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

import assistant.assistant.urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.bot.urls')),
    path('', include('assistant.assistant.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

"""
URL configuration for wordblox project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from wordtag.views import TagViewSet, WordViewSet, SpellinBloxPullHandler, DomainLocker
from utils.tokens import get_csrf_token

router = routers.DefaultRouter()
router.register(r'tags', TagViewSet)
router.register(r'words', WordViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('csrf-token', get_csrf_token),
    path('login', SpellinBloxPullHandler.run),
    path('get_domain_id', DomainLocker.run),
    path('api/', include(router.urls))
]

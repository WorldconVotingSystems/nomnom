"""
URL configuration for nomnom project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from nominate import views
from nominate.apps import convention_configuration

app_urls = (
    f"{convention_configuration().urls_app_name}.urls"
    if convention_configuration().urls_app_name
    else None
)
if app_urls:
    convention_urls = [path("convention/", include(app_urls, namespace="convention"))]
else:
    convention_urls = []

urlpatterns = [
    path("", views.ElectionView.as_view()),
    path("e/", include("nominate.urls", namespace="election")),
    *convention_urls,
    path("admin/", admin.site.urls),
    path("", include("social_django.urls", namespace="social")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("watchman/", include("watchman.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
]

if "hugopacket" in settings.INSTALLED_APPS:
    urlpatterns.append(
        path("p/", include("hugopacket.urls", namespace="hugopacket")),
    )

if settings.DEBUG_TOOLBAR_ENABLED:
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))

handler403 = "nominate.views.access_denied"

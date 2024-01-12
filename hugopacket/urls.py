from django.urls import path

from . import views

app_name = "hugopacket"

urlpatterns = [path("", views.index)]

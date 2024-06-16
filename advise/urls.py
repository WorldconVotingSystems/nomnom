from django.urls import path

from . import views

app_name = "advise"

urlpatterns = [
    path("", views.Index.as_view(), name="advisory_votes"),
    path("<pk>/", views.Vote.as_view(), name="vote"),
]

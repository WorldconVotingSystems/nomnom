from django.urls import path

from . import views

app_name = "hugopacket"

urlpatterns = [
    path("<election_id>/", views.index),
    path(
        "<election_id>/<int:packet_file_id>/",
        views.download_packet,
        name="download_packet",
    ),
]

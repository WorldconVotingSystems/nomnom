from django.urls import path

from . import admin

app_name = "canonicalize"

urlpatterns = [
    path(
        "<int:category_id>/ballots/",
        admin.BallotReportView.as_view(),
        name="ballots",
    ),
    path(
        "<int:category_id>/finalists/",
        admin.finalists,
        name="finalists",
    ),
]

from django.urls import path

from nominate import reports

from . import views

app_name = "nominate"

urlpatterns = [
    path("", views.ElectionView.as_view(), name="index"),
    path(
        "e/<election_id>/",
        views.ElectionModeView.as_view(),
        name="redirect",
    ),
    path(
        "e/<election_id>/nope/",
        views.ClosedElectionView.as_view(),
        name="closed",
    ),
    path("e/<election_id>/nominate/", views.NominationView.as_view(), name="nominate"),
    path("e/<election_id>/vote/", views.VoteView.as_view(), name="vote"),
    path(
        "e/<election_id>/nominations/",
        reports.Nominations.as_view(),
        name="nomination-report",
    ),
    path(
        "e/<election_id>/invalidated-nominations/",
        reports.InvalidatedNominations.as_view(),
        name="invalidated-nomination-report",
    ),
    path(
        "e/<election_id>/email-nominations/",
        views.nominate.EmailNominations.as_view(),
        name="email-my-nominations",
    ),
]

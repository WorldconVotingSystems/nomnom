from django.urls import path

from nominate import reports

from . import views

urlpatterns = [
    path("", views.ElectionView.as_view(), name="election-index"),
    path("welcome/", views.WelcomeView.as_view(), name="election-welcome"),
    path(
        "<election_id>/current/",
        views.ElectionModeView.as_view(),
        name="election-redirect",
    ),
    path(
        "<election_id>/nope/",
        views.ClosedElectionView.as_view(),
        name="closed-election",
    ),
    path("<election_id>/nominate/", views.NominationView.as_view(), name="nominate"),
    path("<election_id>/vote/", views.VoteView.as_view(), name="vote"),
    path(
        "<election_id>/nominations/",
        reports.Nominations.as_view(),
        name="nomination-report",
    ),
]

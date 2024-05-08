from django.urls import path

from . import reports, views

app_name = "nominate"

urlpatterns = [
    # has to come first so that the general <election_id> doesn't match
    path("login_error/", views.login_error, name="login_error"),
    path("", views.ElectionView.as_view(), name="index"),
    path(
        "<election_id>/",
        views.ElectionModeView.as_view(),
        name="redirect",
    ),
    path(
        "<election_id>/nope/",
        views.ClosedElectionView.as_view(),
        name="closed",
    ),
    path("<election_id>/nominate/", views.NominationView.as_view(), name="nominate"),
    path("<election_id>/vote/", views.VoteView.as_view(), name="vote"),
    path(
        "<election_id>/edit_nominating_ballot/<member_id>",
        views.AdminNominationView.as_view(),
        name="edit_nominations",
    ),
    path(
        "<election_id>/edit_voting_ballot/<member_id>",
        views.VoteView.as_view(),
        name="edit_votes",
    ),
    path(
        "<election_id>/nominations/",
        reports.Nominations.as_view(),
        name="nomination-report",
    ),
    path(
        "<election_id>/invalidated-nominations/",
        reports.InvalidatedNominations.as_view(),
        name="invalidated-nomination-report",
    ),
    path(
        "<election_id>/votes/",
        reports.AllVotes.as_view(),
        name="vote-report",
    ),
    path(
        "<election_id>/<category_id>/votes/",
        reports.CategoryVotes.as_view(),
        name="category-vote-report",
    ),
    path(
        "<election_id>/results/",
        views.ElectionResultsPrettyView.as_view(),
        name="category-vote-results",
    ),
    path(
        "<election_id>/invalidated-votes/",
        reports.ElectionResults.as_view(),
        name="results",
    ),
    path(
        "<election_id>/email-nominations/",
        views.nominate.EmailNominations.as_view(),
        name="email-my-nominations",
    ),
    path(
        "<election_id>/email-votes/",
        views.vote.EmailVotes.as_view(),
        name="email-my-votes",
    ),
]

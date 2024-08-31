from django.urls import path

from . import admin, reports, views

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
        views.AdminVoteView.as_view(),
        name="edit_votes",
    ),
    # Report Views
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
    # All Hugo Votes
    path(
        "<election_id>/admin/votes/",
        reports.AllVotes.as_view(),
        name="vote-report",
    ),
    # The result of the Hugo Award elections, as of the present.
    path(
        "<election_id>/admin/results/",
        admin.election_reports,
        name="vote-results",
    ),
    path(
        "<election_id>/admin/results/full/",
        views.ElectionResultsPrettyView.as_view(),
        name="full-vote-results",
    ),
    path(
        "<election_id>/admin/category/<category_id>/all-places/",
        views.CategoryResultsPrettyView.as_view(),
        name="full-vote-all-places",
    ),
    # Email views. These trigger emails to be sent for the user.
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

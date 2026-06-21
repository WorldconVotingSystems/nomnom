import functools
from collections.abc import Callable, Generator
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from attr import dataclass
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.formats import localize
from django.utils.translation import gettext as _
from django_svcs.apps import svcs_from
from ipware import get_client_ip
from pyrankvote.helpers import CandidateStatus, ElectionResults
from render_block import render_block_to_string

from nomnom.convention import HugoAwards
from nomnom.nominate import models
from nomnom.nominate.decorators import user_passes_test_or_forbidden
from nomnom.nominate.forms import RankForm
from nomnom.nominate.hugo_awards import (
    SlantTable,
    get_winners_for_election,
    run_election,
)
from nomnom.nominate.tasks import send_voting_ballot
from nomnom.nominate.templatetags import nomnom_filters
from nomnom.wsfs.rules.constitution_2023 import NoFinalists

if TYPE_CHECKING:
    from django_stubs_ext import _AnyUser as UserModel
else:
    from nomnom.nominate.admin import UserModel  # noqa: F401

from .base import ElectionView, NominatorView


@dataclass
class ElectionStatistics:
    total_voters: int


@dataclass
class CategoryStatistics:
    voters: int


@dataclass(frozen=True)
class BallotFlow:
    profile: models.NominatingMemberProfile
    election: models.Election
    template_name: str
    can_vote: bool
    on_saved: Callable[[HttpRequest, "BallotFlow", bool], None]


def require_profile(user: UserModel) -> models.NominatingMemberProfile:
    try:
        return user.convention_profile
    except models.NominatingMemberProfile.DoesNotExist:
        raise PermissionDenied("You do not have a nominating profile.")


def get_finalists(election: models.Election) -> QuerySet[models.Finalist]:
    return models.Finalist.objects.select_related("category").filter(
        category__election=election
    )


def get_ranks(
    finalists: QuerySet[models.Finalist], profile: models.NominatingMemberProfile
) -> QuerySet[models.Rank]:
    return models.Rank.objects.select_related("finalist__category").filter(
        finalist__in=finalists, membership=profile
    )


def build_voting_context(
    election: models.Election, profile: models.NominatingMemberProfile, form: RankForm
) -> dict[str, any]:
    context = {
        "election": election,
        "categories": models.Category.objects.filter(election=election),
        "form": form,
    }

    return context


@login_required
def voting_ballot(request: HttpRequest, election_id: str) -> HttpResponse:
    election = get_object_or_404(models.Election, slug=election_id)
    profile = require_profile(request.user)
    can_vote = election.user_can_vote(request.user)
    flow = BallotFlow(
        profile=profile,
        election=election,
        template_name="nominate/vote.html"
        if can_vote
        else "nominate/election_closed.html",
        can_vote=can_vote,
        on_saved=lambda req, flow, success: None,
    )
    return _ballot(request, flow)


def _ballot(request: HttpRequest, flow: BallotFlow) -> HttpResponse:
    if request.method == "POST":
        return _submit_ballot(request, flow)

    finalists = get_finalists(flow.election)
    ranks = get_ranks(finalists, flow.profile)

    form = RankForm(
        [],
        finalists=finalists,
        ranks=ranks,
    )

    context = build_voting_context(flow.election, flow.profile, form)
    return TemplateResponse(request, flow.template_name, context)


@transaction.atomic
def _submit_ballot(request: HttpRequest, flow: BallotFlow) -> HttpResponse:
    election = flow.election
    profile = flow.profile

    if not flow.can_vote:
        if election.is_post_voting:
            messages.error(request, f"Voting has closed for {election}")
        else:
            messages.error(request, f"You do not have voting rights for {election}")
        return redirect("election:index")

    finalists = get_finalists(election)
    ranks = get_ranks(finalists, profile)
    client_ip_address, _ = get_client_ip(request=request)
    user_agent = request.headers.get("user-agent")
    form = RankForm(request.POST, finalists=finalists, ranks=ranks)
    context = build_voting_context(election, profile, form)

    if not form.is_valid():
        messages.warning(request, "Something wasn't quite right with your ballot")
        if request.htmx:
            return HttpResponse(
                render_block_to_string(
                    flow.template_name,
                    "form",
                    context=context,
                    request=request,
                )
            )
        else:
            return TemplateResponse(request, flow.template_name, context)

    ranks_to_create = []
    ranks_to_delete = []

    for finalist, vote in form.cleaned_data["votes"].items():
        rank = models.Rank(finalist=finalist, membership=profile)

        if vote is None:
            ranks_to_delete.append(rank)
        else:
            rank.position = int(vote)
            rank.voter_ip_address = client_ip_address
            rank.rank_date = datetime.now(timezone.utc)
            ranks_to_create.append(rank)

    created_ranks = models.Rank.objects.bulk_create(
        ranks_to_create,
        update_conflicts=True,
        unique_fields=["finalist", "membership"],
        update_fields=["position", "voter_ip_address", "rank_date"],
    )

    admin_records = [
        models.RankAdminData(
            rank=rank, ip_address=client_ip_address, user_agent=user_agent
        )
        for rank in created_ranks
    ]
    models.RankAdminData.objects.bulk_create(
        admin_records,
        update_conflicts=True,
        unique_fields=["rank"],
        update_fields=["ip_address", "user_agent"],
    )

    # Find all ranks that are in the ranks_to_delete list in the database
    # using the ORM.
    models.Rank.objects.filter(
        finalist__in=[rank.finalist for rank in ranks_to_delete],
        membership=profile,
    ).delete()

    def on_commit_callback():
        flow.on_saved(request, flow, True)

    transaction.on_commit(on_commit_callback)

    if request.htmx:
        return HttpResponse(
            render_block_to_string(
                flow.template_name,
                "form",
                context=context,
                request=request,
            )
        )
    else:
        return redirect("election:vote", election_id=flow.election.slug)


class EmailVotes(NominatorView):
    def get(self, request: HttpRequest, *args, **kwargs):
        # if the GET request has a .txt extension, render the text template
        # otherwise, render the HTML template
        if request.GET.get("format") == "txt":
            self.template_name = "nominate/email/votes_for_user.txt"
            self.content_type = "text/plain"
        else:
            self.template_name = "nominate/email/votes_for_user.html"
            self.content_type = "text/html"

        finalists = models.Finalist.objects.filter(category__election=self.election())
        ranks = models.Rank.objects.filter(
            finalist__in=finalists, membership=self.profile()
        )

        report_date = datetime.utcnow()
        site_url = Site.objects.get_current().domain
        ballot_path = reverse(
            "election:vote", kwargs={"election_id": self.election().slug}
        )
        ballot_url = f"https://{site_url}{ballot_path}"

        form = RankForm(finalists=finalists, ranks=ranks)
        # run "clean" to populate the form with the existing data and
        # group the finalists by category into display-oriented structures.
        # We're doing a bit of a hack here, because full_clean requires posted
        # data that we don't have, and we're not really validating the form.
        form.cleaned_data = {}
        form.clean()

        return self.render_to_response(
            {
                "report_date": localize(report_date),
                "member": self.profile(),
                "election": self.election(),
                "form": form,
                "ballot_url": ballot_url,
                "message": "This is a test render of the ballot. If you're seeing this, I hope you're having fun poking around at the innards.",
            },
        )

    def post(self, request: HttpRequest, *args, **kwargs):
        send_voting_ballot.delay(self.election().id, self.profile().id)
        messages.success(
            request,
            _(
                "An email will be sent to you with your saved votes. Any unsaved changes on this page will not be included."
            ),
        )

        return redirect("election:vote", election_id=self.election().slug)


def admin_post_save_hook(
    request: HttpRequest, flow: BallotFlow, did_email: bool = False
) -> None:
    if flow.profile.user.email:
        send_voting_ballot.delay(
            flow.election.id,
            flow.profile.id,
            message="An Admin has entered or modified your votes. Please review your ballot if this is unexpected.",
        )
        messages.success(
            request,
            _(
                f"An email will be sent to {flow.profile.user.email} with your changes to their voting ballot"
            ),
        )


@login_required
@user_passes_test_or_forbidden(lambda u: u.is_staff)
@permission_required("nominate.edit_ballot", raise_exception=True)
def voting_ballot_admin(
    request: HttpRequest, election_id: str, member_id: int
) -> HttpResponse:
    election = get_object_or_404(models.Election, slug=election_id)
    profile = get_object_or_404(models.NominatingMemberProfile, id=member_id)
    flow = BallotFlow(
        profile=profile,
        election=election,
        template_name="nominate/admin_vote.html",
        can_vote=True,
        on_saved=admin_post_save_hook,
    )
    return _ballot(request, flow)


# these are probably the wrong tests; what we're going to want is for
# the admin to make the voting page available to the public, but only
# after the election is completed, and _not_ automatically based on
# election state; this should be a manual decision.
#
# That said, for now, we're going to go with the same tests as the
# NominationView, roughly. It's good enough for _during_ the election.
@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_forbidden(lambda u: u.is_staff), name="dispatch")
@method_decorator(
    permission_required("nominate.view_raw_results", raise_exception=True),
    name="dispatch",
)
class ElectionResultsPrettyView(ElectionView):
    template_name = "admin/nominate/election/results.html"

    def get_context_data(self, **kwargs):
        awards = svcs_from(self.request).get(HugoAwards)
        context = super().get_context_data(**kwargs)

        context["is_admin_page"] = True

        winners = get_winners_for_election(awards, self.election())

        context["category_tables"] = {
            c: SlantTable(res.rounds, title="Winner(s)")
            for c, res in winners.items()
            if res is not None
        }

        # load some basic election stats for display
        count_of_members_who_voted = (
            models.Rank.objects.filter(finalist__category__election=self.election())
            .distinct("membership")
            .count()
        )
        context["election_stats"] = ElectionStatistics(
            total_voters=count_of_members_who_voted,
        )

        context["category_stats"] = {
            c: CategoryStatistics(
                voters=models.Rank.objects.filter(finalist__category=c)
                .distinct("membership")
                .count(),
            )
            for c in self.election().category_set.all()
        }

        return context

    def get(self, request, *args, **kwargs) -> HttpResponse:
        return self.render_to_response(self.get_context_data())


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_forbidden(lambda u: u.is_staff), name="dispatch")
@method_decorator(
    permission_required("nominate.view_raw_results", raise_exception=True),
    name="dispatch",
)
class CategoryResultsPrettyView(ElectionView):
    template_name = "admin/nominate/category/results.html"

    @functools.lru_cache
    def category(self):
        return get_object_or_404(models.Category, id=self.kwargs.get("category_id"))

    def get_all_places(self) -> Generator[ElectionResults, None, None]:
        awards = svcs_from(self.request).get(HugoAwards)
        excluded_finalists: list[models.Finalist] = []
        all_finalists = self.category().finalist_set.all()
        candidate_finalists = {f.as_candidate(): f for f in all_finalists}

        # we will run this at most N times, where N is the number of finalists
        for _i in range(len(all_finalists)):
            results = run_election(
                awards, self.category(), excluded_finalists=excluded_finalists
            )
            winning_round = results.rounds[-1]

            winning_votes = int(
                sum(
                    r.number_of_votes
                    for r in winning_round.candidate_results
                    if r.status == CandidateStatus.Elected
                )
            )
            winners = [
                cr.candidate
                for cr in winning_round.candidate_results
                if cr.status == CandidateStatus.Elected
            ]

            yield results

            new_exclusions = [candidate_finalists[c] for c in winners]
            excluded_finalists.extend(new_exclusions)

            # we are done if we have excluded all finalists OR if we have stopped finding
            # winners to exclude, or if there were no votes in the "winning" round.
            if (
                len(excluded_finalists) == len(all_finalists)
                or not winners
                or winning_votes == 0
            ):
                break

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["is_admin_page"] = True
        context["category"] = self.category()
        context["tables"] = [
            SlantTable(res.rounds, title=nomnom_filters.place(i + 1))
            for i, res in enumerate(self.get_all_places())
        ]

        return context

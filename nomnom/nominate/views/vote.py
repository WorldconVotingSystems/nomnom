import functools
from collections.abc import Generator
from datetime import datetime, timezone

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.sites.models import Site
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.formats import localize
from django.utils.translation import gettext as _
from ipware import get_client_ip
from pyrankvote.helpers import CandidateStatus, ElectionResults
from render_block import render_block_to_string

from django_svcs.apps import svcs_from
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
from nomnom.convention import HugoAwards

from .base import ElectionView, NominatorView


class VoteView(NominatorView):
    template_name = "nominate/vote.html"

    def build_ballot_forms(self, data=None) -> RankForm:
        args = [] if data is None else [data]
        return RankForm(*args, finalists=self.finalists(), ranks=self.ranks())

    def finalists(self):
        return models.Finalist.objects.select_related("category").filter(
            category__election=self.election()
        )

    def ranks(self):
        return models.Rank.objects.select_related("finalist__category").filter(
            finalist__in=self.finalists(), membership=self.profile()
        )

    def get_context_data(self, **kwargs):
        form = kwargs.pop("form", None)
        if form is None:
            form = self.build_ballot_forms()
        ctx = {"form": form}
        ctx.update(super().get_context_data(**kwargs))
        return ctx

    def can_vote(self, request):
        return self.election().user_can_vote(request.user)

    def get(self, request: HttpRequest, *args, **kwargs):
        if not self.can_vote(request):
            self.template_name = "nominate/election_closed.html"

        return super().get(request, *args, **kwargs)

    @transaction.atomic
    def post(self, request: HttpRequest, *args, **kwargs):
        if not self.can_vote(request):
            messages.error(
                request, f"You do not have voting rights for {self.election()}"
            )
            return redirect("election:index")

        client_ip_address, _ = get_client_ip(request=request)
        user_agent = self.request.headers.get("user-agent")
        form = self.build_ballot_forms(request.POST)

        if form.is_valid():
            ranks_to_create = []
            ranks_to_delete = []
            for finalist, vote in form.cleaned_data["votes"].items():
                rank = models.Rank(finalist=finalist, membership=self.profile())

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
                membership=self.profile(),
            ).delete()

            def on_commit_callback():
                self.post_save_hook(request)

            transaction.on_commit(on_commit_callback)

            if request.htmx:
                return HttpResponse(
                    render_block_to_string(
                        self.template_name,
                        "form",
                        context=self.get_context_data(form=form),
                        request=request,
                    )
                )
            else:
                return redirect(
                    "election:vote", election_id=self.kwargs.get("election_id")
                )
        else:
            messages.warning(request, "Something wasn't quite right with your ballot")
            if request.htmx:
                return HttpResponse(
                    render_block_to_string(
                        self.template_name,
                        "form",
                        context=self.get_context_data(form=form),
                        request=request,
                    )
                )
            else:
                return self.render_to_response(self.get_context_data(form=form))

    def post_save_hook(self, request: HttpRequest) -> None:
        messages.success(
            request,
            f"Your ballot has been cast as {self.profile().preferred_name} for {self.election()}",
        )


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


class AdminVoteView(VoteView):
    template_name = "nominate/admin_vote.html"

    @method_decorator(login_required)
    @method_decorator(user_passes_test_or_forbidden(lambda u: u.is_staff))
    @method_decorator(permission_required("nominate.edit_ballot", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def can_vote(self, request) -> bool:
        # the rules here are quite different; since the user is an admin, the only barrier is that
        # they must have permissions to change nominations. That is gated in dispatch() so this
        # is always `True`
        return True

    @functools.lru_cache
    def profile(self):
        return get_object_or_404(
            models.NominatingMemberProfile, id=self.kwargs.get("member_id")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_admin_page"] = True
        return ctx

    def post_save_hook(self, request: HttpRequest) -> None:
        if self.profile().user.email:
            send_voting_ballot.delay(
                self.election().id,
                self.profile().id,
                message="An Admin has entered or modified your votes. Please review your ballot if this is unexpected.",
            )
            messages.success(
                request,
                _(
                    f"An email will be sent to {self.profile().user.email} with your changes to their voting ballot"
                ),
            )


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
        context["category_tables"] = {
            c: SlantTable(res.rounds, title="Winner(s)")
            for c, res in get_winners_for_election(awards, self.election()).items()
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

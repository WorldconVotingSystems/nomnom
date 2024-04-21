from datetime import datetime

from django.contrib import messages
from django.contrib.sites.models import Site
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.formats import localize
from django.utils.translation import gettext as _
from ipware import get_client_ip
from render_block import render_block_to_string

from nominate import models
from nominate.forms import RankForm
from nominate.tasks import send_voting_ballot

from .base import NominatorView


class VoteView(NominatorView):
    template_name = "nominate/vote.html"

    def build_ballot_forms(self, data=None) -> RankForm:
        args = [] if data is None else [data]
        return RankForm(*args, finalists=self.finalists(), ranks=self.ranks())

    def finalists(self):
        return models.Finalist.objects.filter(category__election=self.election())

    def ranks(self):
        return models.Rank.objects.filter(
            finalist__in=self.finalists(), membership=self.profile()
        )

    def get_context_data(self, **kwargs):
        form = kwargs.pop("form", None)
        if form is None:
            form = self.build_ballot_forms()
        ctx = {"form": form}
        ctx.update(super().get_context_data(**kwargs))
        return ctx

    def get(self, request: HttpRequest, *args, **kwargs):
        if not self.election().user_can_vote(request.user):
            self.template_name = "nominate/election_closed.html"

        return super().get(request, *args, **kwargs)

    @transaction.atomic
    def post(self, request: HttpRequest, *args, **kwargs):
        if not self.election().user_can_vote(request.user):
            messages.error(
                request, f"You do not have voting rights for {self.election()}"
            )
            return redirect("election:index")

        client_ip_address, _ = get_client_ip(request=request)
        form = self.build_ballot_forms(request.POST)
        if form.is_valid():
            for finalist, vote in form.cleaned_data["votes"].items():
                rank, _ = models.Rank.objects.update_or_create(
                    finalist=finalist, membership=self.profile()
                )
                if vote is None:
                    rank.delete()
                else:
                    rank.position = int(vote)
                    rank.voter_ip_address = client_ip_address
                    rank.save()
            messages.success(
                request,
                f"Your ballot has been cast as {self.profile().preferred_name} for {self.election()}",
            )
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


class AdminVoteView(VoteView): ...


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
            request, _("An email will be sent to you with your voting ballot")
        )

        return redirect("election:vote", election_id=self.election().slug)

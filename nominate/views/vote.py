from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from ipware import get_client_ip
from render_block import render_block_to_string

from nominate import models
from nominate.forms import RankForm

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


class AdminVoteView(VoteView):
    ...

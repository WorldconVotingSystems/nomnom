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
            ranks_to_create = []
            ranks_to_delete = []
            for finalist, vote in form.cleaned_data["votes"].items():
                rank = models.Rank(finalist=finalist, membership=self.profile())
                if vote is None:
                    ranks_to_delete.append(rank)
                else:
                    rank.position = int(vote)
                    rank.voter_ip_address = client_ip_address
                    ranks_to_create.append(rank)

            models.Rank.objects.bulk_create(
                ranks_to_create,
                update_conflicts=True,
                unique_fields=["finalist", "membership"],
                update_fields=["position", "voter_ip_address"],
            )

            # Find all ranks that are in the ranks_to_delete list in the database
            # using the ORM.
            models.Rank.objects.filter(
                finalist__in=[rank.finalist for rank in ranks_to_delete],
                membership=self.profile(),
            ).delete()

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

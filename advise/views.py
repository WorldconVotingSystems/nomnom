# Create your views here.

from functools import lru_cache

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms import Form
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import FormView, ListView
from ipware.ip import get_client_ip
from nominate.models import NominatingMemberProfile
from render_block import render_block_to_string

from . import forms, models


def get_profile(request: HttpRequest, deny=False) -> NominatingMemberProfile | None:
    try:
        profile = request.user.convention_profile
    except models.NominatingMemberProfile.DoesNotExist:
        if deny:
            raise PermissionDenied("You do not have a nominating profile.")
        profile = None

    return profile


class Index(ListView):
    template_name = "advise/index.html"
    model = models.Proposal
    context_object_name = "open_votes"

    def get_queryset(self):
        return models.Proposal.open.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = get_profile(self.request)
        votes = models.Vote.objects.filter(membership=user_profile).select_related(
            "proposal"
        )
        user_votes = {v.proposal.id: v for v in votes}
        context["user_votes"] = user_votes
        return context


@method_decorator(login_required, name="dispatch")
class Vote(FormView):
    template_name = "advise/vote.html"
    model = models.Vote
    context_object_name = "vote"
    form_class = forms.VoteForm

    @lru_cache
    def get_profile(self):
        return get_profile(self.request, deny=True)

    @transaction.atomic
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)

    def form_valid(self, form: Form) -> HttpResponse:
        vote, created = models.Vote.objects.get_or_create(
            membership=self.get_profile(),
            proposal=models.Proposal.objects.get(id=self.kwargs["pk"]),
            defaults={"selection": form.cleaned_data["selection"]},
        )

        if not created:
            vote.selection = form.cleaned_data["selection"]
            vote.save()

        client_ip, _ = get_client_ip(self.request)
        user_agent = self.request.headers.get("user-agent")
        vote.vote_admin_data, created = models.VoteAdminData.objects.get_or_create(
            vote=vote, defaults={"ip_address": client_ip, "user_agent": user_agent}
        )

        if not created:
            vote.vote_admin_data.ip_address = client_ip
            vote.vote_admin_data.user_agent = user_agent

        def successful_vote():
            messages.success(
                self.request,
                f"Your vote of {vote.selection} on {vote.proposal.name} has been recorded",
            )

        transaction.on_commit(successful_vote)

        if self.request.htmx:
            return HttpResponse(
                render_block_to_string(
                    self.template_name, "form", context=self.get_context_data()
                )
            )
        return redirect("advise:index")

    def form_invalid(self, form: Form) -> HttpResponse:
        if self.request.htmx:
            return HttpResponse(
                render_block_to_string(
                    self.template_name, "form", context=self.get_context_data(form=form)
                )
            )
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        advisory_vote = models.Proposal.objects.get(id=self.kwargs["pk"])
        user_vote = models.Vote.objects.filter(
            membership=self.get_profile(), proposal=advisory_vote
        ).first()
        context.update({"advisory_vote": advisory_vote, "user_vote": user_vote})
        return context

# Create your views here.

from functools import lru_cache
from typing import Any, Literal, cast, overload

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms import Form
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import FormView, ListView
from ipware.ip import get_client_ip
from render_block import render_block_to_string

from nomnom.nominate.decorators import (
    request_passes_test_or_forbidden,
    user_passes_test_or_forbidden,
)
from nomnom.nominate.models import NominatingMemberProfile

from . import forms, models


@overload
def get_profile(
    request: HttpRequest, deny: Literal[False] = ...
) -> NominatingMemberProfile | None: ...


@overload
def get_profile(
    request: HttpRequest, deny: Literal[True]
) -> NominatingMemberProfile: ...


def get_profile(request: HttpRequest, deny=False) -> NominatingMemberProfile | None:
    profile = get_user_profile(request.user)
    if deny and profile is None:
        raise PermissionDenied("You do not have a nominating profile.")

    return profile


def get_user_profile(
    user: AbstractBaseUser | AnonymousUser,
) -> NominatingMemberProfile | None:
    if user.is_anonymous:
        return None  # Anonymous users by definition do not have a profile

    try:
        profile = cast(Any, user).convention_profile
    except (models.NominatingMemberProfile.DoesNotExist, AttributeError):
        return None

    return profile


def user_has_a_convention_profile(user) -> bool:
    return get_user_profile(user) is not None


@method_decorator(login_required, name="dispatch")
@method_decorator(
    user_passes_test_or_forbidden(user_has_a_convention_profile), name="dispatch"
)
class Index(ListView):
    template_name = "advise/index.html"
    model = models.Proposal
    context_object_name = "open_votes"

    def get_queryset(self):
        if self.request.user.has_perm("advise.can_preview"):
            return models.Proposal.previewing.all()
        else:
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
@method_decorator(
    user_passes_test_or_forbidden(user_has_a_convention_profile), name="dispatch"
)
@method_decorator(
    request_passes_test_or_forbidden(models.Proposal.is_open_for_user),
    name="dispatch",
)
class Vote(FormView):
    template_name = "advise/vote.html"
    model = models.Vote
    context_object_name = "vote"
    form_class = forms.VoteForm

    @lru_cache
    def get_profile(self) -> NominatingMemberProfile:
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
        return redirect("advise:advisory_votes")

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

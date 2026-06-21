from collections.abc import Callable
from dataclasses import dataclass
from itertools import groupby
from operator import attrgetter
from typing import TYPE_CHECKING, Any

from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from ipware import get_client_ip
from render_block import render_block_to_string

from nomnom.nominate import models

if TYPE_CHECKING:
    from django_stubs_ext import _AnyUser as UserModel
else:
    from nomnom.nominate.admin import UserModel

from nomnom.nominate.decorators import user_passes_test_or_forbidden
from nomnom.nominate.forms import NominationForm
from nomnom.nominate.tasks import link_nominations_to_works, send_ballot


@dataclass(frozen=True)
class BallotFlow:
    profile: models.NominatingMemberProfile
    election: models.Election
    template_name: str
    can_nominate: bool
    on_saved: Callable[[HttpRequest, "BallotFlow", bool], None]


def require_profile(user: UserModel) -> models.NominatingMemberProfile:
    try:
        return user.convention_profile
    except models.NominatingMemberProfile.DoesNotExist:
        raise PermissionDenied("You do not have a nominating profile.")


def build_nominating_context(
    election: models.Election,
    profile: models.NominatingMemberProfile,
    form: NominationForm,
) -> dict[str, Any]:
    nomination_groups = groupby(
        profile.nomination_set.filter(category__election=election),
        attrgetter("category"),
    )
    nominations = {cat: list(noms) for cat, noms in nomination_groups}

    context: dict[str, Any] = {
        "election": election,
        "categories": models.Category.objects.filter(election=election),
        "nominations": nominations,
        "form": form,
    }

    if nominations:
        context["most_recent"] = (
            profile.nomination_set.filter(category__election=election)
            .latest("nomination_date")
            .nomination_date
        )

    return context


def get_template_name(election: models.Election, user: UserModel) -> str:
    can_nominate = election.user_can_nominate(user)

    if can_nominate:
        return "nominate/nominate.html"
    elif election.nominations_have_closed():
        return "nominate/show_nominations.html"
    else:
        return "nominate/election_closed.html"


def initial_nomination_form(
    election: models.Election,
    profile: models.NominatingMemberProfile,
) -> NominationForm:
    return NominationForm(
        categories=list(models.Category.objects.filter(election=election)),
        queryset=profile.nomination_set.filter(category__election=election),
    )


def submitted_nomination_form(
    request: HttpRequest, election: models.Election
) -> NominationForm:
    return NominationForm(
        categories=list(models.Category.objects.filter(election=election)),
        data=request.POST,
    )


def member_post_save_hook(
    request: HttpRequest, flow: BallotFlow, did_email: bool = False
) -> None:
    message = "Your set of nominations was saved"
    if did_email:
        message += " and an email with your ballot will be sent to you"
    messages.success(request, message)


@login_required
def nominating_ballot(request: HttpRequest, election_id: str) -> HttpResponse:
    election = get_object_or_404(models.Election, slug=election_id)
    profile = require_profile(request.user)
    flow = BallotFlow(
        profile=profile,
        election=election,
        template_name=get_template_name(election, request.user),
        can_nominate=election.user_can_nominate(request.user),
        on_saved=member_post_save_hook,
    )

    return _ballot(request, flow)


def _ballot(request: HttpRequest, flow: BallotFlow) -> HttpResponse:
    if request.method == "POST":
        return _submit_ballot(request, flow)

    form = initial_nomination_form(flow.election, flow.profile)
    context = build_nominating_context(flow.election, flow.profile, form)
    return TemplateResponse(request, flow.template_name, context)


def _render_form_block(
    request: HttpRequest, flow: BallotFlow, form: NominationForm
) -> HttpResponse:
    context = build_nominating_context(flow.election, flow.profile, form)
    return HttpResponse(
        render_block_to_string(
            flow.template_name,
            "form",
            context=context,
            request=request,
        )
    )


@transaction.atomic
def _submit_ballot(request: HttpRequest, flow: BallotFlow) -> HttpResponse:
    election = flow.election
    profile = flow.profile

    if not flow.can_nominate:
        if election.nominations_have_closed():
            messages.error(request, _("Nominations have closed for this election"))
        else:
            messages.error(
                request,
                f"You do not have nominating rights for {election}",
            )
        return redirect("election:index")

    form = submitted_nomination_form(request, election)

    if not form.is_valid():
        messages.warning(request, "Something wasn't quite right with your ballot")
        if request.htmx:
            return _render_form_block(request, flow, form)

        context = build_nominating_context(election, profile, form)
        return TemplateResponse(request, flow.template_name, context)

    client_ip_address, _ignored = get_client_ip(request=request)
    should_email = "save_and_email" in request.POST

    # first, we clear all of the existing nominations for this user and election; they've
    # submitted a new ballot, so we're going to start from scratch.
    profile.nomination_set.filter(category__election=election).delete()

    # now, we're going to iterate through the formsets and save the nominations
    for nomination in form.cleaned_data["nominations"]:
        nomination.nominator = profile
        nomination.nomination_ip_address = client_ip_address
    nominations = models.Nomination.objects.bulk_create(
        form.cleaned_data["nominations"]
    )

    def on_commit_callback():
        link_nominations_to_works.delay([n.pk for n in nominations])
        if should_email:
            send_ballot.delay(election.id, profile.id)

        flow.on_saved(request, flow, should_email)

    transaction.on_commit(on_commit_callback)

    if request.htmx:
        return _render_form_block(request, flow, form)

    # Kind of hacky but works - the place on the page is passed in the submit
    category_saved = request.POST.get("save_all", None)
    url = reverse(
        "election:nominate",
        kwargs={"election_id": election.slug},
    )
    anchor = f"#{category_saved}"
    return redirect(f"{url}{anchor}")


def admin_post_save_hook(
    request: HttpRequest, flow: BallotFlow, did_email: bool = False
) -> None:
    if flow.profile.user.email:
        send_ballot.delay(
            flow.election.id,
            flow.profile.id,
            message="An Admin has entered or modified your nominations. Please review your ballot if this is unexpected.",
        )

        messages.success(
            request,
            _(
                f"An email will be sent to {flow.profile.user.email} with your changes to their ballot"
            ),
        )


@login_required
@user_passes_test_or_forbidden(lambda u: u.is_staff)
@permission_required("nominate.edit_ballot", raise_exception=True)
def admin_nomination_view(
    request: HttpRequest, election_id: str, member_id: int
) -> HttpResponse:
    election = get_object_or_404(models.Election, slug=election_id)
    profile = get_object_or_404(models.NominatingMemberProfile, id=member_id)
    flow = BallotFlow(
        profile=profile,
        election=election,
        template_name="nominate/admin_nominate.html",
        can_nominate=True,
        on_saved=admin_post_save_hook,
    )

    return _ballot(request, flow)

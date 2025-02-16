import functools
from datetime import datetime
from itertools import groupby
from operator import attrgetter

from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from ipware import get_client_ip
from render_block import render_block_to_string

from nomnom.nominate import models
from nomnom.nominate.decorators import user_passes_test_or_forbidden
from nomnom.nominate.forms import NominationForm
from nomnom.nominate.tasks import link_nominations_to_works, send_ballot

from .base import NominatorView


class NominationView(NominatorView):
    template_name = "nominate/nominate.html"

    def get_context_data(self, **kwargs):
        nominations = kwargs.pop("nominations", None)
        most_recent: datetime | None = None
        if nominations is None:
            if self.profile() and self.election():
                nominations = groupby(
                    self.profile().nomination_set.filter(
                        category__election=self.election()
                    ),
                    attrgetter("category"),
                )
                nominations = {cat: list(noms) for cat, noms in nominations}
                if nominations:
                    most_recent = (
                        self.profile()
                        .nomination_set.filter(category__election=self.election())
                        .latest("nomination_date")
                    ).nomination_date
        form = kwargs.pop("form", None)
        if form is None:
            form = NominationForm(
                categories=list(self.categories()),
                queryset=self.profile().nomination_set.filter(
                    category__election=self.election()
                ),
            )
        ctx = {
            "form": form,
            "nominations": nominations,
            "most_recent": most_recent,
        }
        ctx.update(super().get_context_data(**kwargs))
        return ctx

    def can_nominate(self, request) -> bool:
        return self.election().user_can_nominate(request.user)

    def get_template_names(self) -> list[str]:
        if self.can_nominate(self.request):
            return super().get_template_names()

        if self.election().nominations_have_closed():
            return ["nominate/show_nominations.html"]

        return ["nominate/election_closed.html"]

    @transaction.atomic
    def post(self, request: HttpRequest, *args, **kwargs):
        if not self.can_nominate(request):
            if self.election().nominations_have_closed():
                messages.error(request, _("Nominations have closed for this election"))
            else:
                messages.error(
                    request, f"You do not have nominating rights for {self.election()}"
                )
            return redirect("election:index")

        profile = self.profile()
        client_ip_address, _ignored = get_client_ip(request=request)

        # Kind of hacky but works - the place on the page is passwed in the submit
        category_saved = request.POST.get("save_all", None)

        form = NominationForm(categories=list(self.categories()), data=request.POST)

        if form.is_valid():
            # first, we clear all of the existing nominations for this user and election; they've
            # submitted a new ballot, so we're going to start from scratch.
            profile.nomination_set.filter(category__election=self.election()).delete()

            # now, we're going to iterate through the formsets and save the nominations
            for nomination in form.cleaned_data["nominations"]:
                nomination.nominator = profile
                nomination.nomination_ip_address = client_ip_address
            nominations = models.Nomination.objects.bulk_create(
                form.cleaned_data["nominations"]
            )

            def on_commit_callback():
                link_nominations_to_works.delay([n.pk for n in nominations])
                self.post_save_hook(request)

            transaction.on_commit(on_commit_callback)

            if request.htmx:
                return HttpResponse(
                    render_block_to_string(
                        "nominate/nominate.html",
                        "form",
                        context=self.get_context_data(form=form),
                        request=request,
                    )
                )
            else:
                url = reverse(
                    "election:nominate",
                    kwargs={"election_id": self.kwargs.get("election_id")},
                )
                anchor = f"#{category_saved}"
                return redirect(f"{url}{anchor}")

        else:
            messages.warning(request, "Something wasn't quite right with your ballot")
            if request.htmx:
                return HttpResponse(
                    render_block_to_string(
                        "nominate/nominate.html",
                        "form",
                        context=self.get_context_data(form=form),
                        request=request,
                    )
                )
            else:
                return self.render_to_response(self.get_context_data(form=form))

    def post_save_hook(self, request: HttpRequest) -> None:
        messages.success(request, "Your set of nominations was saved")


class AdminNominationView(NominationView):
    template_name = "nominate/admin_nominate.html"

    @method_decorator(login_required)
    @method_decorator(user_passes_test_or_forbidden(lambda u: u.is_staff))
    @method_decorator(permission_required("nominate.edit_ballot", raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def can_nominate(self, request) -> bool:
        # the rules here are quite different; since the user is an admin, the only barrier is that
        # they must have permissions to change nominations. That is gated in dispatch() so this
        # is always `True`
        return True

    @functools.lru_cache
    def profile(self) -> models.NominatingMemberProfile:
        return get_object_or_404(
            models.NominatingMemberProfile, id=self.kwargs.get("member_id")
        )

    def post_save_hook(self, request: HttpRequest) -> None:
        if self.profile().user.email:
            send_ballot.delay(
                self.election().id,
                self.profile().id,
                message="An Admin has entered or modified your nominations. Please review your ballot if this is unexpected.",
            )
            messages.success(
                request,
                _(
                    f"An email will be sent to {self.profile().user.email} with your changes to their ballot"
                ),
            )


class EmailNominations(NominatorView):
    def post(self, request: HttpRequest, *args, **kwargs):
        send_ballot.delay(
            self.election().id,
            self.profile().id,
        )
        messages.success(request, _("An email will be sent to you with your ballot"))

        return redirect("election:nominate", election_id=self.kwargs.get("election_id"))

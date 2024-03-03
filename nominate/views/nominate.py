import functools

from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from ipware import get_client_ip
from render_block import render_block_to_string

from nominate import models
from nominate.forms import NominationForm
from nominate.tasks import send_ballot

from .base import NominatorView


class NominationView(NominatorView):
    template_name = "nominate/nominate.html"

    def get_context_data(self, **kwargs):
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
        }
        ctx.update(super().get_context_data(**kwargs))
        return ctx

    def get(self, request: HttpRequest, *args, **kwargs):
        if not self.election().user_can_nominate(request.user):
            self.template_name = "nominate/election_closed.html"
            self.extra_context = {"object": self.election()}

        return super().get(request, *args, **kwargs)

    @transaction.atomic
    def post(self, request: HttpRequest, *args, **kwargs):
        if not self.election().user_can_nominate(request.user):
            messages.error(
                request, f"You do not have nominating rights for {self.election()}"
            )
            return redirect("election:index")

        profile = self.profile()
        client_ip_address, _ = get_client_ip(request=request)

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
            models.Nomination.objects.bulk_create(form.cleaned_data["nominations"])
            messages.success(request, "Your set of nominations was saved")

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


class AdminNominationView(NominationView):
    template_name = "nominate/admin_nominate.html"

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.is_staff))
    @method_decorator(permission_required("nominate.change_nomination"))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @functools.lru_cache
    def profile(self):
        return get_object_or_404(
            models.NominatingMemberProfile, id=self.kwargs.get("member_id")
        )


class EmailNominations(NominatorView):
    def post(self, request: HttpRequest, *args, **kwargs):
        send_ballot.delay(
            self.election().id,
            self.profile().id,
        )
        messages.success(request, _("An email will be sent to you with your ballot"))

        return redirect("election:nominate", election_id=self.kwargs.get("election_id"))

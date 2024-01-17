from collections.abc import Iterable

from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from ipware import get_client_ip
from render_block import render_block_to_string

from nominate import forms, models


def get_categories(election_id: str) -> Iterable[models.Category]:
    return models.Category.objects.filter(election__slug=election_id)


@transaction.atomic
def save_nominations(request: HttpRequest, election_id) -> HttpResponse:
    election = get_object_or_404(models.Election, slug=election_id)
    categories = get_categories(election_id=election_id)

    context = {}
    form = forms.NominationForm(categories=categories, data=request.POST)

    profile = request.user.convention_profile
    client_ip_address, _ = get_client_ip(request=request)

    if form.is_valid():
        # first, we clear all of the existing nominations for this user and election; they've
        # submitted a new ballot, so we're going to start from scratch.
        profile.nomination_set.filter(category__election=election).delete()

        # now, we're going to iterate through the formsets and save the nominations
        for nomination in form.cleaned_data["nominations"]:
            nomination.nominator = profile
            nomination.ip_address = client_ip_address
        models.Nomination.objects.bulk_create(form.cleaned_data["nominations"])
        messages.success(request, "Your set of nominations was saved")

        context["form"] = forms.NominationForm(
            categories=categories,
            queryset=profile.nomination_set.filter(
                category__election=election,
            ),
        )

    else:
        context["form"] = form
        messages.warning(request, "Something wasn't quite right with your ballot")

    html = render_block_to_string(
        "nominate/nominate.html", "form", context=context, request=request
    )
    return HttpResponse(html)

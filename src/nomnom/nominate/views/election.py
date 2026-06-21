from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse

from nomnom.nominate import models


@login_required
def election_list(request: HttpRequest) -> HttpResponse:
    elections = models.Election.enrich_with_user_data(
        models.Election.objects.all(), request
    )
    return TemplateResponse(
        request, "nominate/election_list.html", {"election_list": elections}
    )


@login_required
def election_mode_redirect(request: HttpRequest, election_id: str) -> HttpResponse:
    election = get_object_or_404(models.Election, slug=election_id)
    if election.user_can_nominate(request.user):
        return redirect(
            "election:nominate",
            permanent=False,
            election_id=election.slug,
        )

    if election.user_can_vote(request.user):
        return redirect(
            "election:vote",
            permanent=False,
            election_id=election.slug,
        )

    return redirect(
        "election:closed",
        permanent=False,
        election_id=election.slug,
    )


def election_closed(request: HttpRequest, election_id: str) -> HttpResponse:
    election = get_object_or_404(models.Election, slug=election_id)
    return TemplateResponse(
        request, "nominate/election_closed.html", {"election": election}
    )

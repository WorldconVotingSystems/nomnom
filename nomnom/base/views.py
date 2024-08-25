from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

import nomnom.advise.models
import nomnom.nominate.models


def index(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        context = {
            "object_list": nomnom.nominate.models.Election.enrich_with_user_data(
                nomnom.nominate.models.Election.objects.all(), request
            ),
            "proposals": nomnom.advise.models.Proposal.open.all(),
        }
    else:
        context = {}
    return render(request, "nomnom/index.html", context)

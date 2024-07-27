from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

import advise.models
import nominate.models


def index(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        context = {
            "object_list": nominate.models.Election.enrich_with_user_data(
                nominate.models.Election.objects.all(), request
            ),
            "proposals": advise.models.Proposal.open.all(),
        }
    else:
        context = {}
    return render(request, "nomnom/index.html", context)

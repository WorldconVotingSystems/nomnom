from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from nomnom.base.signals import index_content_load


def index(request: HttpRequest) -> HttpResponse:
    context = {}
    if request.user.is_authenticated:
        for receiver, response in index_content_load.send(sender=None, request=request):
            if isinstance(response, dict):
                context.update(response)

    return render(request, "nomnom/index.html", context)

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from hugopacket.models import Packets


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "hugopacket/index.html", {"packets": Packets.objects.all()})

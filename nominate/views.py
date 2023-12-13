from typing import Any
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from nominate import models


class ElectionView(ListView):
    model = models.Election


class ElectionModeView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args: Any, **kwargs: Any) -> str | None:
        election = get_object_or_404(models.Election, slug=kwargs.get("slug"))
        match election.state:
            case models.Election.Mode.PRE_NOMINATING:
                return reverse("closed-election", kwargs={"slug": election.slug})

            case models.Election.Mode.NOMINATING:
                return reverse("nominate", kwargs={"slug": election.slug})

            case models.Election.Mode.VOTING:
                return reverse("vote", kwargs={"slug": election.slug})

            case models.Election.Mode.CLOSED:
                return reverse("closed-election", kwargs={"slug": election.slug})
        raise Exception("WTF")


class ClosedElectionView(DetailView):
    model = models.Election

    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        self.election = get_object_or_404(models.Election, slug=slug)


class NominationView(ListView):
    model = models.Nomination

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        self.election = get_object_or_404(models.Election, slug=slug)

    def post(self, request: HttpRequest, slug: str) -> HttpResponse:
        self.election = get_object_or_404(models.Election, slug=slug)


class VoteView(TemplateView):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        self.election = get_object_or_404(models.Election, slug=slug)

    def post(self, request: HttpRequest, slug: str) -> HttpResponse:
        self.election = get_object_or_404(models.Election, slug=slug)

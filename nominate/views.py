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
        election = get_object_or_404(models.Election, slug=kwargs.get("election_id"))
        match election.state:
            case "pre_nominating":
                return reverse("closed-election", kwargs={"election_id": election.slug})

            case "nominating":
                return reverse("nominate", kwargs={"election_id": election.slug})

            case "voting":
                return reverse("vote", kwargs={"election_id": election.slug})

            case "closed":
                return reverse("closed-election", kwargs={"election_id": election.slug})

            case _:
                return reverse("closed-election", kwargs={"election_id": election.slug})


class ClosedElectionView(DetailView):
    model = models.Election
    slug_url_kwarg = "election_id"
    template_name_suffix = "_closed"


class NominationView(TemplateView):
    model = models.Nomination

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        print(":::> got here")
        return super().get_context_data(
            election=get_object_or_404(models.Election, slug=kwargs.get("election_id"))
        )


class VoteView(TemplateView):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request: HttpRequest, election_id: str) -> HttpResponse:
        self.election = get_object_or_404(models.Election, slug=election_id)

    def post(self, request: HttpRequest, election_id: str) -> HttpResponse:
        self.election = get_object_or_404(models.Election, slug=election_id)

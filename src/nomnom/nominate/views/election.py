from collections.abc import Iterable
from typing import Any

import django.contrib.auth.forms
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView

from nomnom.nominate import models


class ElectionView(ListView):
    model = models.Election

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if settings.NOMNOM_ALLOW_USERNAME_LOGIN_FOR_MEMBERS:
            context["form"] = django.contrib.auth.forms.AuthenticationForm()

        return context

    def get_queryset(self):
        query_set: Iterable[models.Election] = super().get_queryset()

        return models.Election.enrich_with_user_data(query_set, self.request)


class ElectionModeView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args: Any, **kwargs: Any) -> str | None:
        election = get_object_or_404(models.Election, slug=kwargs.get("election_id"))
        if election.user_can_nominate(self.request.user):
            return reverse("election:nominate", kwargs={"election_id": election.slug})

        if election.user_can_vote(self.request.user):
            return reverse("election:vote", kwargs={"election_id": election.slug})

        return reverse("election:closed", kwargs={"election_id": election.slug})


class ClosedElectionView(DetailView):
    model = models.Election
    slug_url_kwarg = "election_id"
    template_name_suffix = "_closed"

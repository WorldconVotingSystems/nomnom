from collections.abc import Iterable
from typing import Any

import django.contrib.auth.forms
from django.apps import apps
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView
from django_svcs.apps import svcs_from
from nomnom.convention import ConventionConfiguration

from nominate import models


class ElectionView(ListView):
    model = models.Election

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if settings.NOMNOM_ALLOW_USERNAME_LOGIN_FOR_MEMBERS:
            context["form"] = django.contrib.auth.forms.AuthenticationForm()

        return context

    def get_queryset(self):
        query_set: Iterable[models.Election] = super().get_queryset()

        # we only do this if the convention has a packet setting
        convention_configuration = svcs_from(self.request).get(ConventionConfiguration)

        ElectionPacket = None
        # if the packet application is installed and enabled, let's try load the model here
        if (
            "hugopacket" in settings.INSTALLED_APPS
            and convention_configuration.packet_enabled
        ):
            app_config = apps.get_app_config("hugopacket")
            ElectionPacket = app_config.models_module.ElectionPacket

        # annotate our elections with some info
        for election in query_set:
            election.is_open_for_user = election.is_open_for(self.request.user)
            election.user_state = election.describe_state(user=self.request.user)
            election.user_pretty_state = election.pretty_state(user=self.request.user)

            if ElectionPacket:
                try:
                    packet = ElectionPacket.objects.filter(election=election).first()
                except ElectionPacket.DoesNotExist:
                    packet = None
                election.packet_exists = packet is not None
                election.packet_is_ready = packet and (
                    packet.enabled
                    or self.request.user.has_perm("hugopacket.preview_packet")
                )
            else:
                election.packet_exists = False

        return query_set


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

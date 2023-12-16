import functools
from typing import Any
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from nominate import models
from nominate.forms import NominationFormset


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
    template_name = "nominate/nominate.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @functools.lru_cache
    def election(self):
        return get_object_or_404(models.Election, slug=self.kwargs.get("election_id"))

    @functools.lru_cache
    def categories(self):
        return models.Category.objects.filter(election=self.election())

    @functools.lru_cache
    def profile(self):
        try:
            profile = self.request.user.nominator_profile
        except models.NominatingMemberProfile.DoesNotExist:
            raise PermissionDenied()

        return profile

    def build_ballot_forms(self):
        return {
            category: NominationFormset(
                self.request.POST,
                self.request.FILES,
                form_kwargs={"category": category},
                queryset=models.Nomination.objects.filter(
                    category=category, nominator=self.profile()
                ),
                prefix=str(category.id),
            )
            for category in self.categories()
        }

    def get_context_data(self, **kwargs):
        ctx = {"formsets": self.build_ballot_forms()}
        ctx.update(super().get_context_data(**kwargs))
        return ctx

    def post(self, request: HttpRequest, *args, **kwargs):
        profile = self.profile()
        had_errors = False
        for category in self.categories():
            formset = NominationFormset(
                request.POST,
                request.FILES,
                form_kwargs={"category": category},
                prefix=str(category.id),
            )
            if formset.is_valid():
                for nomination_record in formset.save(commit=False):
                    nomination_record.category = category
                    nomination_record.nominator = profile
                    nomination_record.save()

            else:
                had_errors = True

        if not had_errors:
            return redirect("nominate", election_id=self.kwargs.get("election_id"))
        else:
            return self.get(request, *args, **kwargs)


class VoteView(TemplateView):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request: HttpRequest, election_id: str) -> HttpResponse:
        self.election = get_object_or_404(models.Election, slug=election_id)

    def post(self, request: HttpRequest, election_id: str) -> HttpResponse:
        self.election = get_object_or_404(models.Election, slug=election_id)

import functools
from typing import Any
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView, TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from nominate import models
from nominate.forms import NominationFormset
from ipware import get_client_ip


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


class NominatorView(TemplateView):
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


class WelcomeView(NominatorView):
    template_name = "nominate/welcome.html"


class NominationView(NominatorView):
    template_name = "nominate/nominate.html"

    def build_ballot_forms(self, data=None):
        args = [] if data is None else [data]
        return {
            category: NominationFormset(
                *args,
                form_kwargs={"category": category},
                queryset=models.Nomination.objects.filter(
                    category=category, nominator=self.profile()
                ),
                prefix=str(category.id),
            )
            for category in self.categories()
        }

    def get_context_data(self, **kwargs):
        formsets = kwargs.pop("formsets", None)
        if formsets is None:
            formsets = self.build_ballot_forms()
        ctx = {"formsets": formsets}
        ctx.update(super().get_context_data(**kwargs))
        return ctx

    def get(self, request: HttpRequest, *args, **kwargs):
        if not self.election().is_nominating:
            self.template_name = "nominate/election_closed.html"
            self.extra_context = {"object": self.election()}

        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs):
        profile = self.profile()
        had_errors = False
        client_ip_address, _ = get_client_ip(request=request)
        formsets = {
            category: NominationFormset(
                request.POST,
                request.FILES,
                form_kwargs={"category": category},
                prefix=str(category.id),
            )
            for category in self.categories()
        }

        for category, formset in formsets.items():
            if formset.is_valid():
                for nomination_record in formset.save(commit=False):
                    nomination_record.category = category
                    nomination_record.nominator = profile
                    nomination_record.nomination_ip_address = client_ip_address
                    nomination_record.save()
            else:
                had_errors = True

        if not had_errors:
            messages.success(request, "Your set of nominations was saved")
            return redirect("nominate", election_id=self.kwargs.get("election_id"))
        else:
            messages.warning(request, "Something wasn't quite right with your ballot")
            return self.render_to_response(self.get_context_data(formsets=formsets))


class VoteView(TemplateView):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request: HttpRequest, election_id: str) -> HttpResponse:
        self.election = get_object_or_404(models.Election, slug=election_id)

    def post(self, request: HttpRequest, election_id: str) -> HttpResponse:
        self.election = get_object_or_404(models.Election, slug=election_id)


def access_denied(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    return render(request, "nominate/forbidden.html")

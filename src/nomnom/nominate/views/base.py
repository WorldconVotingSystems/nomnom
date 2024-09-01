import functools

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from nomnom.nominate import models


class ElectionView(TemplateView):
    @functools.lru_cache
    def election(self):
        return get_object_or_404(models.Election, slug=self.kwargs.get("election_id"))

    @functools.lru_cache
    def categories(self):
        return models.Category.objects.filter(election=self.election())

    def get_context_data(self, **kwargs):
        ctx = {
            "election": self.election,
            "categories": self.categories,
        }
        ctx.update(super().get_context_data(**kwargs))
        return ctx


class NominatorView(ElectionView):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        ctx = {
            "profile": self.profile,
        }
        ctx.update(super().get_context_data(**kwargs))
        return ctx

    @functools.lru_cache
    def profile(self) -> models.NominatingMemberProfile:
        try:
            profile = self.request.user.convention_profile
        except models.NominatingMemberProfile.DoesNotExist:
            raise PermissionDenied("You do not have a nominating profile.")

        return profile


def access_denied(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    return render(request, "nominate/forbidden.html", status=403)


def login_error(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    return render(request, "registration/auth_error.html", status=401)

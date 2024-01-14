import functools

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from nominate import models


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

    def get_context_data(self, **kwargs):
        ctx = {
            "election": self.election,
            "categories": self.categories,
            "profile": self.profile,
        }
        ctx.update(super().get_context_data(**kwargs))
        return ctx

    @functools.lru_cache
    def profile(self) -> models.NominatingMemberProfile:
        try:
            profile = self.request.user.convention_profile
        except models.NominatingMemberProfile.DoesNotExist:
            raise PermissionDenied()

        return profile


def access_denied(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    return render(request, "nominate/forbidden.html")


def login_error(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    return render(request, "registration/auth_error.html")

import csv
from typing import Any
from django.contrib.auth.decorators import permission_required, user_passes_test
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.shortcuts import get_object_or_404
from django.db.models import F
import functools
from nominate import models


report_decorators = [
    user_passes_test(lambda u: u.is_staff, login_url="/admin/login/"),
    permission_required("nominate.report"),
]


@method_decorator(report_decorators, name="get")
class Nominations(View):
    content_type = "text/csv"
    context_object_name = "nominations"
    template_name = "nominate/report/nominations.csv"
    csv_filename = "nomination-report.csv"
    extra_fields = ["email", "member_number"]

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super().dispatch(request, *args, **kwargs)

    @functools.lru_cache
    def election(self):
        return get_object_or_404(models.Election, slug=self.kwargs.get("election_id"))

    def query_set(self):
        return models.Nomination.objects.select_related("nominator__user").annotate(
            preferred_name=F("nominator__preferred_name"),
            member_number=F("nominator__member_number"),
            username=F("nominator__user__username"),
            email=F("nominator__user__email"),
        )

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{self.csv_filename}"'
        writer = csv.writer(response)

        # Header
        queryset = self.query_set()
        # Write CSV header
        field_names = [
            field.name for field in queryset.model._meta.fields
        ] + self.extra_fields
        writer = csv.writer(response)
        writer.writerow([field for field in field_names])

        # Write data rows
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

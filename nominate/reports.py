import csv
import functools
from abc import abstractmethod
from io import StringIO
from typing import Any

from django.contrib.auth.decorators import permission_required, user_passes_test
from django.db.models import F, Q, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import View

from nominate import models

report_decorators = [
    user_passes_test(lambda u: u.is_staff, login_url="/admin/login/"),
    permission_required("nominate.report"),
]


class ReportWriter:
    @abstractmethod
    def add_header(self, field_names) -> "ReportWriter":
        ...

    @abstractmethod
    def add_row(self, row) -> "ReportWriter":
        ...

    def build(self) -> Any:
        ...


class CSVWriter(ReportWriter):
    ...


class Report:
    @abstractmethod
    def query_set(self) -> QuerySet:
        ...

    def get_content_type(self) -> str:
        return getattr(self, "content_type", "text/csv")

    def get_filename(self) -> str:
        if hasattr(self, "filename"):
            return self.filename.format(self=self)

        return "report.csv"

    def get_extra_fields(self) -> list[str]:
        return getattr(self, "extra_fields", [])

    def get_field_names(self) -> list[str]:
        query_set = self.query_set()
        return [
            field.name for field in query_set.model._meta.fields
        ] + self.get_extra_fields()

    def build_report_header(self, writer) -> None:
        writer.writerow(self.get_field_names())

    def build_report(self, writer) -> None:
        query_set = self.query_set()
        field_names = self.get_field_names()

        self.build_report_header(writer)

        for obj in query_set:
            writer.writerow([getattr(obj, field) for field in field_names])

    def get_report_header(self) -> str:
        string = StringIO()
        writer = csv.writer(string)
        self.build_report_header(writer)
        return string.getvalue()

    def get_report_content(self) -> str:
        string = StringIO()
        writer = csv.writer(string)
        self.build_report(writer)
        return string.getvalue()


class NominationsReport(Report):
    extra_fields = ["email", "member_number"]
    content_type = "text/csv"
    filename = "nomination-report.csv"

    def __init__(self, election: models.Election):
        self.election = election

    def query_set(self) -> QuerySet:
        return (
            models.Nomination.objects.filter(category__election=self.election)
            .select_related("nominator__user", "category")
            .annotate(
                preferred_name=F("nominator__preferred_name"),
                member_number=F("nominator__member_number"),
                username=F("nominator__user__username"),
                email=F("nominator__user__email"),
                admin_id=F("admin__id"),
                valid=F("admin__valid_nomination"),
            )
            .filter(Q(valid=True) | Q(admin_id=None))
        )


class InvalidatedNominationsReport(Report):
    extra_fields = ["email", "member_number"]
    content_type = "text/csv"
    filename = "invalidated-nomination-report.csv"

    def __init__(self, election: models.Election):
        self.election = election

    def query_set(self) -> QuerySet:
        return (
            models.Nomination.objects.filter(category__election=self.election)
            .select_related("nominator__user", "category")
            .annotate(
                preferred_name=F("nominator__preferred_name"),
                member_number=F("nominator__member_number"),
                username=F("nominator__user__username"),
                email=F("nominator__user__email"),
                admin_id=F("admin__id"),
                valid=F("admin__valid_nomination"),
            )
            .filter(Q(valid=False))
        )


@method_decorator(report_decorators, name="get")
class NominationsReportView(View):
    def get_report_class(self):
        return getattr(self, "report_class", NominationsReport)

    @functools.lru_cache
    def election(self) -> models.Election:
        return get_object_or_404(models.Election, slug=self.kwargs.get("election_id"))

    @functools.lru_cache
    def report(self) -> Report:
        return self.get_report_class()(election=self.election())

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        report = self.report()
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="{report.get_filename()}"'
        writer = csv.writer(response)

        report.build_report(writer)

        return response


class Nominations(NominationsReportView):
    report_class = NominationsReport


class InvalidatedNominations(NominationsReportView):
    report_class = InvalidatedNominationsReport

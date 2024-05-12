import csv
import functools
from abc import abstractmethod
from collections.abc import Iterable
from datetime import UTC, datetime
from io import StringIO
from itertools import groupby
from pathlib import Path
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
    def add_header(self, field_names) -> "ReportWriter": ...

    @abstractmethod
    def add_row(self, row) -> "ReportWriter": ...

    def build(self) -> Any: ...


class CSVWriter(ReportWriter): ...


class Report:
    @abstractmethod
    def query_set(self) -> QuerySet: ...

    def get_content_type(self) -> str:
        return getattr(self, "content_type", "text/csv")

    def get_filename(self) -> str:
        if hasattr(self, "filename"):
            base_filename = self.filename.format(self=self)
        else:
            base_filename = "report.csv"

        basename, ext = Path(base_filename).stem, Path(base_filename).suffix

        return f"{basename}-{datetime.now(UTC).strftime('%Y-%m-%d')}{ext}"

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

    def __init__(self, election: models.Election):
        self.election = election

    @property
    def filename(self) -> str:
        return f"{self.election.slug}-nomination-report.csv"

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


class VotingReport(Report):
    def __init__(self, category: models.Category):
        self.category = category
        self.election = category.election

    @property
    def filename(self) -> str:
        return f"{self.election.slug}-{self.category.id}-voting-report.csv"

    def query_set(self) -> QuerySet:
        return models.Rank.objects.filter(
            finalist__category=self.category
        ).select_related("membership__user", "finalist")

    def get_finalists(self) -> Iterable[models.Finalist]:
        return (
            models.Finalist.objects.filter(category=self.category)
            .order_by("category__ballot_position", "ballot_position")
            .all()
        )

    def get_field_names(self):
        # The field names are: the member ID, the member name, one per finalist. The question is...
        # do we want one report per category, or one overall report?
        finalists = self.get_finalists()
        return [
            "member_id",
            "name",
        ] + [f.name for f in finalists]

    def process(self, query_set: QuerySet) -> Iterable[Any]:
        # The queryset is per-finalist-rank. What we want is per-member, with columns for each
        # finalist. The finalist columns _must be stable_; we can't rely on the order of the
        # queryset. so we'll depend on the built in ballot order for both the finalists and the
        # categories. Also, because it's possible for a member not to have ranked a finalist, we get
        # our finalist list from the category set, not the query set.
        sorted_by_member = query_set.order_by(
            "membership", "finalist__category__ballot_position"
        )

        grouper: Iterable[
            tuple[models.NominatingMemberProfile, Iterable[models.Rank]]
        ] = groupby(sorted_by_member, key=lambda x: x.membership)
        for member, rows in grouper:
            yield [member.member_number, member.preferred_name] + [
                pos for _, pos in self.ranks_for_member(rows)
            ]

    def ranks_for_member(
        self, rows: Iterable[models.Rank]
    ) -> list[tuple[models.Finalist, int | None]]:
        rfm = {r.finalist: r.position for r in rows}
        return [(f, rfm.get(f)) for f in self.get_finalists()]

    def build_report(self, writer) -> None:
        query_set = self.query_set()

        self.build_report_header(writer)

        for obj in self.process(query_set):
            writer.writerow(obj)


class InvalidatedNominationsReport(Report):
    extra_fields = ["email", "member_number"]
    content_type = "text/csv"

    def __init__(self, election: models.Election):
        self.election = election

    @property
    def filename(self) -> str:
        return f"{self.election.slug}-invalidated-nomination-report.csv"

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
class ElectionReportView(View):
    is_attachment: bool = True
    content_type: str = "text/csv"

    def get_report_class(self):
        return getattr(self, "report_class", NominationsReport)

    @functools.lru_cache
    def election(self) -> models.Election:
        return get_object_or_404(models.Election, slug=self.kwargs.get("election_id"))

    @functools.lru_cache
    def report(self) -> Report:
        return self.get_report_class()(self.report_object())

    def get_writer(self, response) -> Any:
        return csv.writer(response)

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        report = self.report()
        response = HttpResponse(content_type=self.content_type)
        if self.is_attachment:
            response["Content-Disposition"] = (
                f'attachment; filename="{report.get_filename()}"'
            )

        report.build_report(self.get_writer(response))

        return response


class Nominations(ElectionReportView):
    report_class = NominationsReport

    def report_object(self):
        return self.election()


class InvalidatedNominations(ElectionReportView):
    report_class = InvalidatedNominationsReport

    def report_object(self):
        return self.election()


class AllVotes(ElectionReportView):
    content_type = "text/plain"
    is_attachment = False
    report_class = VotingReport

    def category(self):
        if "category_id" in self.kwargs:
            return get_object_or_404(models.Category, id=self.kwargs.get("category_id"))
        elif "election_id" in self.kwargs:
            election = get_object_or_404(
                models.Election, slug=self.kwargs.get("election_id")
            )
            category = election.category_set.first()
            return category

    def report_object(self):
        return self.category()


class CategoryVotes(ElectionReportView):
    content_type = "text/plain"
    is_attachment = False

    report_class = VotingReport

    @functools.lru_cache
    def category(self) -> models.Category:
        return get_object_or_404(models.Category, id=self.kwargs.get("category_id"))

    @functools.lru_cache
    def report(self) -> Report:
        return VotingReport(category=self.category())


class ElectionResults(ElectionReportView):
    report_class = InvalidatedNominationsReport

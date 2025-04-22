import csv
import functools
from abc import abstractmethod
from collections.abc import Generator, Iterable
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import Any

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import render
from django.views.generic import View


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

    def build_report_header(self) -> str:
        out = StringIO()
        csv.writer(out).writerow(self.get_field_names())
        return out.getvalue()

    def build_report(self, header=True) -> Generator[str, None, None]:
        if header:
            yield self.build_report_header()

        for row in self.get_report_rows():
            out = StringIO()
            writer = csv.writer(out)
            writer.writerow(row)
            yield out.getvalue()

    def get_report_header(self) -> str:
        return self.build_report_header()

    def get_report_rows(self) -> Generator[list[Any], None, None]:
        query_set = self.query_set()
        field_names = self.get_field_names()

        for obj in self.process(query_set):
            yield self.get_report_row(field_names, obj)

    def get_report_content(self) -> str:
        return "".join(self.build_report())

    def get_report_row(self, field_names: list[str], row: Any) -> list[Any]:
        return [getattr(row, field) for field in field_names]

    def process(self, query_set: QuerySet) -> Iterable[Any]:
        yield from query_set


class ReportView(View):
    is_attachment: bool = True
    content_type: str = "text/csv"
    html_template_name: str | None = None

    def get_report_class(self):
        report_class = getattr(self, "report_class")
        if report_class is None:
            raise Exception(f"No report_class defined for {self.__class__}")

        return report_class

    @functools.lru_cache
    def report(self) -> Report:
        return self.prepare_report()

    def prepare_report(self):
        return self.get_report_class()()

    def get_writer(self, response) -> Any:
        return csv.writer(response)

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        report = self.report()
        if (
            self.html_template_name is not None
            and self.request.GET.get("html") == "true"
        ):
            return self.render_report_in_page(
                request, self.html_template_name, report, *args, **kwargs
            )
        else:
            return self.get_raw_report_response(request, report, *args, **kwargs)

    def get_raw_report_response(
        self, request: HttpRequest, report: Report, *args, **kwargs
    ) -> HttpResponse:
        response = HttpResponse(report.build_report(), content_type=self.content_type)
        if self.is_attachment:
            response["Content-Disposition"] = (
                f'attachment; filename="{report.get_filename()}"'
            )
        return response

    def render_report_in_page(
        self,
        request: HttpRequest,
        html_template_name: str,
        report: Report,
        *args,
        **kwargs,
    ):
        # report_content = StringIO()
        report_content = report.get_report_content()

        return render(
            request,
            html_template_name,
            {
                "report": report,
                "report_content": report_content,
            },
        )

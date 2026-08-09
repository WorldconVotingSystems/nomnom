import csv
from abc import abstractmethod
from collections.abc import Generator, Iterable
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import Any

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


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


# View utilities for reporting
def get_raw_report_response(
    request: HttpRequest,
    report: Report,
    content_type: str = "text/csv",
    is_attachment: bool = True,
) -> HttpResponse:
    response = HttpResponse(
        report.build_report(), content_type=report.get_content_type()
    )
    if is_attachment:
        response["Content-Disposition"] = (
            f'attachment; filename="{report.get_filename()}"'
        )
    return response


def render_report_in_page(
    request: HttpRequest,
    report: Report,
    template_name: str,
    content_type: str = "text/html",
) -> HttpResponse:
    report_content = report.get_report_content()

    return render(
        request,
        template_name,
        {
            "report": report,
            "report_content": report_content,
        },
        content_type=content_type,
    )

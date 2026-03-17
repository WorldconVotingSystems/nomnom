import contextvars
import csv
import functools
import io
from collections import Counter
from collections.abc import Iterable
from itertools import groupby
from typing import Any
from urllib.parse import urlencode

import sentry_sdk
from django import forms
from django.contrib import admin, messages
from django.contrib.auth.decorators import permission_required, user_passes_test
from django.db import IntegrityError, transaction
from django.db.models import Count, F, Q, QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_admin_action_forms import (
    AdminActionForm,
    AdminActionFormsMixin,
    action_with_form,
)
from waffle.decorators import waffle_switch

from nomnom.canonicalize import models
from nomnom.canonicalize.feature_switches import (
    SWITCH_FINALIST_CSV_TABLE,
    SWITCH_SANKEY_DIAGRAM,
)
from nomnom.canonicalize.sankey import transform_eph_to_sankey
from nomnom.nominate import models as nominate
from nomnom.reporting import Report, ReportView
from nomnom.wsfs.rules import eph
from nomnom.wsfs.rules.constitution_2023 import CountData

# This contextvar is used to plumb the current request down into the rendering for the list view
# template, which otherwise can't see it. That allows the view code to make the button include a
# return to the current URL.
_current_request: contextvars.ContextVar[HttpRequest] = contextvars.ContextVar(
    "_current_request"
)


class RemoveCanonicalizationForm(AdminActionForm):
    class Meta:
        help_text = "Remove canonicalization from these nominations?"
        list_objects = True


@action_with_form(RemoveCanonicalizationForm, description="Remove Canonicalization")
def remove_canonicalization(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet, data: dict
) -> None:
    with transaction.atomic():
        models.remove_canonicalization(queryset)


class GroupNominationsForm(AdminActionForm):
    template = "canonicalize/group_nominations_action_form.html"

    work_selection = forms.CharField(required=True)
    work_search = forms.ModelChoiceField(
        required=False,
        queryset=models.Work.objects.order_by("name"),
        label="",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__post_init__(self.modeladmin, self.request, self.queryset)

    def clean_work_selection(self):
        value = self.cleaned_data.get("work_selection", "")

        # "search" sentinel means the autocomplete radio was selected;
        # read the actual pk from the work_search field.
        if value == "search":
            search_pk = self.data.get("work_search", "")
            if search_pk:
                value = f"work:{search_pk}"

        if value.startswith("work:"):
            try:
                pk = int(value.removeprefix("work:"))
                return ("work", models.Work.objects.get(pk=pk))
            except (ValueError, models.Work.DoesNotExist):
                raise forms.ValidationError("Selected work not found.")
        elif value.startswith("nomination:"):
            try:
                pk = int(value.removeprefix("nomination:"))
                return ("nomination", nominate.Nomination.objects.get(pk=pk))
            except (ValueError, nominate.Nomination.DoesNotExist):
                raise forms.ValidationError("Selected nomination not found.")
        raise forms.ValidationError("Please select a work or nomination.")

    def action_form_view(self, request, extra_context=None):
        return super().action_form_view(
            request,
            extra_context={
                "matching_works": self.matching_works,
                **(extra_context or {}),
            },
        )

    def __post_init__(
        self, modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
    ):
        categories = {n.category for n in queryset}
        # only look at works associated with the current selected
        # nominations' categories.
        #
        # It is an error to attempt to group nominations from more than one
        # election together
        elections = {category.election for category in categories}

        if not elections:
            raise forms.ValidationError(
                "You must select at least one nomination to group"
            )

        if len(elections) > 1:
            raise forms.ValidationError(
                "The nominations selected must come from exactly one election"
            )

        similarity_totals: dict[int, float] = {}
        similarity_counts: dict[int, int] = {}
        works_by_pk: dict[int, models.Work] = {}
        nomination_count = queryset.count()
        for nomination in queryset:
            works = models.Work.find_fuzzy_matches(
                nomination.proposed_work_name(), nomination.category
            )
            for work in works:
                similarity_totals[work.pk] = (
                    similarity_totals.get(work.pk, 0) + work.similarity
                )
                similarity_counts[work.pk] = similarity_counts.get(work.pk, 0) + 1
                works_by_pk[work.pk] = work

        avg_similarity: dict[int, float] = {
            pk: similarity_totals[pk] / nomination_count for pk in works_by_pk
        }
        self.matching_works = sorted(
            works_by_pk.values(), key=lambda w: avg_similarity[w.pk], reverse=True
        )
        for work in self.matching_works:
            work.similarity_pct = round(avg_similarity[work.pk] * 100)

    class Meta:
        help_text = "Select work to group under"
        fieldsets = [(None, {"fields": ["work_selection", "work_search"]})]
        autocomplete_fields = ["work_search"]


@action_with_form(
    GroupNominationsForm, description="Group nominations as a single Work"
)
def group_works(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet, data: dict
) -> None:
    selection_type, selection_obj = data.get("work_selection")

    with transaction.atomic():
        if selection_type == "work":
            work = models.group_nominations(queryset, selection_obj)
        elif selection_type == "nomination":
            work = models.Work.objects.create(
                name=selection_obj.proposed_work_name(),
                category=selection_obj.category,
            )
            work = models.group_nominations(queryset, work)
        else:
            raise ValueError("Invalid selection type")
        work.save()


class AllNominationsTableInline(admin.TabularInline):
    model = models.CanonicalizedNomination
    extra = 0
    fields = []
    readonly_fields = ["proposed_work_name", "nominator", "category"]
    list_select_related = (
        "nomination",
        "nomination__nominator",
        "nomination__category",
    )

    has_change_permission = has_add_permission = lambda *args, **kwargs: False

    def proposed_work_name(self, instance: models.CanonicalizedNomination):
        return instance.nomination.canonicalization_display_name()

    def nominator(self, instance: models.CanonicalizedNomination):
        return instance.nomination.nominator

    def category(self, instance):
        return instance.nomination.category

    def get_fields(self, request: HttpRequest, obj):
        """Only return readonly fields

        This tabular view by default tries to show the referenced objects, even if fields
        is empty; I don't want that here."""
        return self.get_readonly_fields(request, obj)


class ElectionFilter(admin.SimpleListFilter):
    title = _("Election")
    parameter_name = "election"

    def lookups(self, request, model_admin):
        return nominate.Election.objects.values_list("slug", "name")

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(category__election__slug=self.value())


class CategoryFilter(admin.SimpleListFilter):
    title = _("Category")
    parameter_name = "category"

    def lookups(self, request, model_admin):
        qs = nominate.Category.objects
        if "election" in request.GET:
            qs = qs.filter(election__slug=request.GET["election"])
        return qs.values_list("id", "name")

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(category__id=self.value())


class WorksChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.name} ({obj.nominations.count()} nominations)"


class CombineWorksForm(AdminActionForm):
    class Meta:
        help_text = "Combine these works? Select one to be the primary work."

    primary_work = WorksChoiceField(
        required=False, queryset=models.Work.objects.all(), widget=forms.RadioSelect
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__post_init__(self.modeladmin, self.request, self.queryset)

    def __post_init__(
        self, modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
    ):
        self.fields["primary_work"].queryset = queryset.annotate(
            nominations_count=Count("nominations")
        ).order_by("-nominations_count", "name")
        self.fields["primary_work"].initial = self.fields[
            "primary_work"
        ].queryset.first()


@action_with_form(CombineWorksForm, description="Combine Works")
def combine_works(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet, data: dict
) -> None:
    with transaction.atomic():
        primary_work: models.Work = data.get("primary_work") or queryset.first()
        primary_work.combine_works(queryset.exclude(pk=primary_work.pk))


class WorkAdmin(AdminActionFormsMixin, admin.ModelAdmin):
    list_display = ["name", "category", "nominations_count"]
    fields = ["name", "category", "notes"]
    list_filter = list_filter = [
        ElectionFilter,
        CategoryFilter,
    ]
    search_fields = ["name"]

    actions = [combine_works]

    inlines = [AllNominationsTableInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return (
            super()
            .get_queryset(request)
            .annotate(nominations_count=Count("nominations"))
            .order_by("category", "name")
        )

    @admin.display(description="Nominations", ordering="nominations_count")
    def nominations_count(self, obj):
        return obj.nominations_count


class CanonicalizedFilter(admin.SimpleListFilter):
    title = _("Canonicalized?")
    parameter_name = "canonicalized"

    def lookups(self, request, model_admin):
        return [("yes", _("Yes")), ("no", _("No"))]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(~Q(works=None))
        elif self.value() == "no":
            return queryset.filter(works=None)


class NominationGroupingView(AdminActionFormsMixin, admin.ModelAdmin):
    model = models.CanonicalizedNomination

    list_display = [
        "proposed_work_name",
        "matched_work",
        "category",
        "has_matched_work",
        "is_recategorized",
        "matched_work_category",
    ]

    list_filter = [
        CanonicalizedFilter,
        ElectionFilter,
        CategoryFilter,
    ]

    actions = [group_works, remove_canonicalization]

    def get_queryset(self, request: HttpRequest) -> QuerySet[nominate.Nomination]:
        _current_request.set(request)

        return nominate.Nomination.objects.select_related(
            "canonicalizednomination",
            "canonicalizednomination__work",
            "canonicalizednomination__work__category",
            "canonicalizednomination__nomination",
            "canonicalizednomination__nomination__category",
        ).order_by("field_1")

    @admin.display(description="Raw Nomination", ordering="field_1")
    def proposed_work_name(self, obj):
        return obj.canonicalization_display_name()

    @admin.display(description="Original Category")
    def category(self, obj):
        return obj.category

    @admin.display(description="Canonicalized?", boolean=True)
    def has_matched_work(self, obj):
        return obj.work is not None

    @admin.display(description="Recategorized?", boolean=True)
    def is_recategorized(self, obj):
        return obj.work is not None and obj.category != obj.work.category

    @admin.display(description="Canonical Work", ordering="works__name")
    def matched_work(self, obj):
        if obj.work is not None:
            link = reverse("admin:canonicalize_work_change", args=[obj.work.id])
            return format_html(
                '<a href="{}">{}</a>',
                link,
                obj.work.name,
            )
        else:
            return self.make_work_button(obj)

    def matched_work_category(self, obj):
        if obj.work:
            return obj.work.category

    def make_work_button(self, obj):
        # Create an HTTP button that triggers the canonicalize:match-work view with the selected row
        if obj.work is None:
            action_url = reverse(
                "canonicalize:make-work", args=[obj.category.id, obj.id]
            )
            query_params = urlencode({"next": self.get_admin_url_with_filters()})
            full_url = f"{action_url}?{query_params}"
            return format_html(
                '<a class="button" href="{}">Create Work</a>',
                full_url,
            )

    def get_action_choices(self, request):
        choices = super().get_action_choices(request)

        # pop the first is the BLANK_CHOICE_DASH
        choices.pop(0)

        # re-order the list so that 'group_works' is first, since it's the most commonly used action
        # and we want to minimize clicks.
        choices.sort(key=lambda choice: 0 if choice[0] == "group_works" else 1)

        return choices

    def changelist_view(self, request, extra_context=None):
        """Override changelist_view to store the request query parameters for reuse."""
        _current_request.set(request)
        return super().changelist_view(request, extra_context)

    def get_admin_url_with_filters(self):
        request = _current_request.get(None)

        return request.get_full_path() if request else ""


# Register your models here.
admin.site.register(models.Work, WorkAdmin)
admin.site.register(models.CanonicalizedNomination, NominationGroupingView)

report_decorators = [
    user_passes_test(lambda u: u.is_staff, login_url="/admin/login/"),
    permission_required("nominate.report"),
]


class BallotReport(Report):
    def __init__(self, category: nominate.Category):
        self.category = category

    @property
    def filename(self) -> str:
        return f"{self.category.election}-{self.category.id}-canonical-ballots.csv"

    def get_field_names(self) -> list[str]:
        return ["nominator", "work 1", "work 2", "work 3", "work 4", "work 5"]

    def query_set(self) -> QuerySet:
        """Return all valid nominations that have been canonicalized.

        For that purpose, we're hinging off the canonicalized ballot join table."""
        return (
            models.CanonicalizedNomination.objects.select_related(
                "nomination",
                "nomination__nominator",
                "nomination__category",
                "nomination__admin",
                "work",
                "work__category",
            )
            .annotate(
                admin_id=F("nomination__admin__id"),
                valid=F("nomination__admin__valid_nomination"),
            )
            .filter(
                work__category=self.category,
            )
            .filter(
                Q(valid=True) | Q(admin_id=None),
            )
            .order_by("nomination__nominator")
        )

    def process(self, query_set: QuerySet) -> Iterable[Any]:
        def _sub_process():
            grouper = groupby(query_set, lambda r: r.nomination.nominator)
            for nominator, rows in grouper:
                yield [nominator] + [r.work for r in rows]

        return _sub_process()

    def get_report_row(self, field_names: list[str], row: Any) -> list[Any]:
        return row


# custom views for EPH and Finalists
@method_decorator(report_decorators, name="get")
class BallotReportView(ReportView):
    report_class = BallotReport
    html_template_name = "canonicalize/ballots.html"

    @functools.lru_cache
    def category(self) -> nominate.Category:
        return get_object_or_404(nominate.Category, pk=self.kwargs.get("category_id"))

    def prepare_report(self):
        return self.get_report_class()(self.category())


@user_passes_test(lambda u: u.is_staff, login_url="/admin/login/")
@permission_required("nominate.report")
def finalists(request: HttpRequest, category_id: int) -> HttpResponse:
    category = get_object_or_404(nominate.Category, pk=category_id)
    ballot_builder = BallotReport(category)
    ballot_objs = [r[1:] for r in ballot_builder.get_report_rows()]
    ballots = [[w.name for w in ballot] for ballot in ballot_objs]

    steps = []

    def recorder(
        ballots: list[str], counts: dict[str, CountData], eliminations: list[str]
    ):
        steps.append((ballots, counts, eliminations))

    finalists = eph(ballots, finalist_count=6, record_steps=recorder)
    return render(
        request,
        "canonicalize/eph.html",
        {
            "category": category,
            "finalists": finalists,
            "steps": steps,
        },
    )


def build_eph_csv(ballots: list[list[str]], finalist_count: int = 6) -> str:
    """Run EPH on *ballots* and return the elimination report as a CSV string.

    Columns: Candidate, Final Score, Number of Ballots, Round 1 … Round N-1, Finalists.

    *Final Score* is the candidate's point total in the last round they appear
    (i.e. at elimination or in the finalists round).  *Number of Ballots* is the
    raw count of ballots the candidate appeared on before EPH processing.
    """
    steps: list[tuple[list, dict[str, CountData], list[str]]] = []
    appearances = Counter()

    for ballot in ballots:
        for work in ballot:
            appearances[work] += 1

    def recorder(
        ballots: list[str], counts: dict[str, CountData], eliminations: list[str]
    ):
        steps.append((ballots, counts, eliminations))

    eph(ballots, finalist_count=finalist_count, record_steps=recorder)

    # Determine the last round each candidate appears in counts (for sorting).
    # Finalists appear in the final step; eliminated candidates disappear after
    # their elimination round.
    last_seen_round: dict[str, int] = {}
    all_candidates_set: set[str] = set()
    for round_idx, (_ballots, counts, _eliminations) in enumerate(steps):
        for name in counts:
            last_seen_round[name] = round_idx
            all_candidates_set.add(name)

    # Sort: candidates who survived longest first, then alphabetically for ties.
    all_candidates = sorted(
        all_candidates_set, key=lambda name: (-last_seen_round[name], name)
    )

    num_rounds = len(steps)

    # Build the CSV.
    output = io.StringIO()
    writer = csv.writer(output)

    # Header: last round is "Finalists" since it shows only the final redistributed scores.
    header = ["Candidate", "Final Score", "Number of Ballots"] + [
        f"Round {i + 1}" for i in range(num_rounds - 1)
    ]
    if num_rounds > 0:
        header.append("Finalists")
    writer.writerow(header)

    # Data rows: show the candidate's points in every round where they appear in
    # counts. Blank cells after the candidate is no longer present.
    for name in all_candidates:
        # Start with the name, and a placeholder for "Final Score" column, which is just the points
        # from the last round they appear in.
        row: list[str | int | None] = [name, None]

        # add a "number of ballots the work appears on" column.
        row.append(appearances[name])

        for _ballots, counts, _eliminations in steps:
            if name in counts:
                row.append(counts[name].points)
                row[1] = counts[name].points
            else:
                break  # candidate eliminated; leave remaining cells blank
        writer.writerow(row)

    return output.getvalue()


@waffle_switch(SWITCH_FINALIST_CSV_TABLE)
@user_passes_test(lambda u: u.is_staff, login_url="/admin/login/")
@permission_required("nominate.report")
def finalists_csv(request: HttpRequest, category_id: int) -> HttpResponse:
    category = get_object_or_404(nominate.Category, pk=category_id)
    ballot_builder = BallotReport(category)
    ballot_objs = [r[1:] for r in ballot_builder.get_report_rows()]
    ballots = [[w.name for w in ballot] for ballot in ballot_objs]

    csv_content = build_eph_csv(ballots)

    filename = f"{category.election}-{category.id}-eph-elimination.csv"
    response = HttpResponse(csv_content, content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@waffle_switch(SWITCH_SANKEY_DIAGRAM)
@user_passes_test(lambda u: u.is_staff, login_url="/admin/login/")
@permission_required("nominate.report")
def sankey_view(request: HttpRequest, category_id: int) -> HttpResponse:
    """HTML page for EPH Sankey diagram visualization.

    The page fetches its data from the sankey_data_view endpoint client-side.
    """
    category = get_object_or_404(nominate.Category, pk=category_id)
    mode = request.GET.get("mode", "compact")
    if mode not in ["compact", "full"]:
        mode = "compact"

    data_url = reverse("canonicalize:sankey-data", args=[category_id])

    return render(
        request,
        "canonicalize/sankey.html",
        {
            "category": category,
            "mode": mode,
            "data_url": data_url,
        },
    )


@waffle_switch(SWITCH_SANKEY_DIAGRAM)
@user_passes_test(lambda u: u.is_staff, login_url="/admin/login/")
@permission_required("nominate.report")
def sankey_data_view(request: HttpRequest, category_id: int) -> JsonResponse:
    """JSON API endpoint returning Sankey diagram data for a category.

    Query parameters:
        mode: 'compact' (default) or 'full'
    """
    category = get_object_or_404(nominate.Category, pk=category_id)
    mode = request.GET.get("mode", "compact")
    if mode not in ["compact", "full"]:
        mode = "compact"

    try:
        ballot_builder = BallotReport(category)
        ballot_objs = [r[1:] for r in ballot_builder.get_report_rows()]
        ballots = [[w.name for w in ballot] for ballot in ballot_objs]

        steps = []

        def recorder(
            ballots: list[str], counts: dict[str, CountData], eliminations: list[str]
        ):
            steps.append((ballots, counts, eliminations))

        finalist_works = eph(ballots, finalist_count=6, record_steps=recorder)
        sankey_data = transform_eph_to_sankey(steps, finalist_works, mode=mode)

        return JsonResponse(sankey_data)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return JsonResponse({"error": str(e)}, status=500)


@user_passes_test(lambda u: u.is_staff, login_url="/admin/login/")
@permission_required("nominate.report")
def make_work(request: HttpRequest, category_id: int, nominee_id: int) -> HttpResponse:
    category = get_object_or_404(nominate.Category, pk=category_id)
    nominee = get_object_or_404(nominate.Nomination, pk=nominee_id)

    reload_nominee = False

    with transaction.atomic():
        work = models.Work.objects.create(
            name=nominee.proposed_work_name(), category=category
        )
        try:
            models.CanonicalizedNomination.objects.create(nomination=nominee, work=work)
        except IntegrityError:
            reload_nominee = True

    if reload_nominee:
        nominee = get_object_or_404(nominate.Nomination, pk=nominee_id)
        if nominee.work is None:
            # set a message
            messages.error(request, "The nomination could not be canonicalized.")
            sentry_sdk.capture_message(
                "Nomination canonicalization failed",
                level="error",
                extra={"nominee_id": nominee_id},
            )

    next_url = request.GET.get("next")

    if next_url:
        # if we have a next, use that:
        return redirect(next_url)
    else:
        # just redirect to the the canonicalize work change page. This does not need
        # to be generic.
        return redirect("admin:canonicalize_work_change", work.id)

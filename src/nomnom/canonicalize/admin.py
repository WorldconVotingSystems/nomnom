import functools
from collections.abc import Iterable
from itertools import groupby
from typing import Any
from urllib.parse import urlencode

from django import forms
from django.contrib import admin
from django.contrib.auth.decorators import permission_required, user_passes_test
from django.db import transaction
from django.db.models import Count, F, Q, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_admin_action_forms import AdminActionForm, action_with_form

from nomnom.canonicalize import models
from nomnom.nominate import models as nominate
from nomnom.reporting import Report, ReportView
from nomnom.wsfs.rules import eph
from nomnom.wsfs.rules.constitution_2023 import CountData


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
    work = forms.ModelChoiceField(
        required=False,
        queryset=models.Work.objects.order_by("name"),
        empty_label="Create New Work from Nominations",
        help_text="Select an existing work to group these nominations into. Leave blank to create a new Work",
    )

    def __post_init__(
        self, modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
    ):
        # only look at works associated with the current selected
        # nominations' categories.
        #
        # It is an error to attempt to group nominations from more than one
        # election together
        elections = {n.category.election for n in queryset}

        if len(elections) != 1:
            raise forms.ValidationError(
                "The nominations selected must come from exactly one election"
            )

        election = elections.pop()
        first_nomination = queryset.first()

        self.fields["work"].queryset = (
            self.fields["work"]
            .queryset.filter(category__election=election)
            .order_by("name")
        )

        if first_nomination:
            work = models.Work.find_match_based_on_identical_nomination(
                first_nomination.proposed_work_name(), first_nomination.category
            )

            if work:
                self.fields["work"].initial = work

    class Meta:
        list_objects = True
        autocomplete_fields = ["work"]
        help_text = "Group these nominations?"


@action_with_form(
    GroupNominationsForm, description="Group nominations as a single Work"
)
def group_works(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet, data: dict
) -> None:
    work = data.get("work")

    with transaction.atomic():
        work = models.group_nominations(queryset, work)
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


class WorkAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "nominations_count"]
    fields = ["name", "category", "notes"]
    list_filter = list_filter = [
        ElectionFilter,
        CategoryFilter,
    ]

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


class NominationGroupingView(admin.ModelAdmin):
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
        self.request = request
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

    def changelist_view(self, request, extra_context=None):
        """Override changelist_view to store the request query parameters for reuse."""
        self.request = request
        return super().changelist_view(request, extra_context)

    def get_admin_url_with_filters(self):
        return self.request.get_full_path() if hasattr(self, "request") else ""


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


@user_passes_test(lambda u: u.is_staff, login_url="/admin/login/")
@permission_required("nominate.report")
def make_work(request: HttpRequest, category_id: int, nominee_id: int) -> HttpResponse:
    category = get_object_or_404(nominate.Category, pk=category_id)
    nominee = get_object_or_404(nominate.Nomination, pk=nominee_id)
    work = models.Work.objects.create(
        name=nominee.proposed_work_name(), category=category
    )
    models.CanonicalizedNomination.objects.create(nomination=nominee, work=work)
    next_url = request.GET.get("next")

    if next_url:
        # if we have a next, use that:
        return redirect(next_url)
    else:
        # just redirect to the the canonicalize work change page. This does not need
        # to be generic.
        return redirect("admin:canonicalize_work_change", work.id)

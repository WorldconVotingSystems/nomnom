from django import forms
from django.contrib import admin
from django.db import transaction
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_admin_action_forms import AdminActionForm, action_with_form

from nomnom.canonicalize import models
from nomnom.nominate import models as nominate


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
        queryset=models.Work.objects.all(),
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

        self.fields["work"].queryset = models.Work.objects.filter(
            category__election=election
        )

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
    readonly_fields = ["proposed_work_name", "category"]

    has_change_permission = has_add_permission = lambda *args, **kwargs: False

    def proposed_work_name(self, instance):
        return instance.nomination.proposed_work_name()

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


class WorkAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "nominations_count"]
    fields = ["name", "category", "notes"]
    list_filter = list_filter = [
        ElectionFilter,
        CategoryFilter,
    ]

    inlines = [AllNominationsTableInline]

    def nominations_count(self, obj):
        return obj.nominations.count()


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
        "category",
        "has_matched_work",
        "is_recategorized",
        "matched_work",
        "matched_work_category",
    ]

    list_filter = [
        CanonicalizedFilter,
        ElectionFilter,
        CategoryFilter,
    ]

    actions = [group_works, remove_canonicalization]

    def get_queryset(self, request: HttpRequest) -> QuerySet[nominate.Nomination]:
        return nominate.Nomination.objects.select_related(
            "canonicalizednomination",
            "canonicalizednomination__work",
        ).order_by("field_1")

    @admin.display(description="Raw Nomination")
    def proposed_work_name(self, obj):
        return obj.proposed_work_name()

    @admin.display(description="Original Category")
    def category(self, obj):
        return obj.category

    @admin.display(description="Canonicalized?", boolean=True)
    def has_matched_work(self, obj):
        return obj.work is not None

    @admin.display(description="Recategorized?", boolean=True)
    def is_recategorized(self, obj):
        return obj.work is not None and obj.category != obj.work.category

    @admin.display(description="Canonical Work")
    def matched_work(self, obj):
        if obj.work is not None:
            link = reverse("admin:canonicalize_work_change", args=[obj.work.id])
            return format_html(
                '<a href="{}">{}</a>',
                link,
                obj.work.name,
            )
        else:
            return "-"

    def matched_work_category(self, obj):
        if obj.work:
            return obj.work.category


# Register your models here.
admin.site.register(models.Work, WorkAdmin)
admin.site.register(models.CanonicalizedNomination, NominationGroupingView)

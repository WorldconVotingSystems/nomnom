from textwrap import dedent
from typing import Any
from urllib.parse import parse_qs

import markdown
from admin_auto_filters.filters import AutocompleteFilter
from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import ForeignKey, QuerySet
from django.db.models.fields.related import RelatedField
from django.forms import ModelChoiceField
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.safestring import mark_safe

from nomnom.nominate.decorators import user_passes_test_or_forbidden

from . import models

UserModel = get_user_model()


# Yeah, I'm sorry about this name too.
class NominationAdminDataAdmin(admin.StackedInline):
    model = models.NominationAdminData


@admin.action(description="Invalidate Selected Nominations")
def invalidate_nomination(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
) -> None:
    set_validation(queryset, False)


@admin.action(description="Validate Selected Nominations")
def validate_nomination(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
) -> None:
    set_validation(queryset, True)


def set_validation(queryset: QuerySet, valid: bool) -> None:
    # update the ones that have admin data already
    models.NominationAdminData.objects.filter(nomination__in=queryset).update(
        valid_nomination=valid
    )

    # find the ones that don't already have info
    nomination_without_admin = queryset.exclude(admin__isnull=False)

    # create the missing ones
    models.NominationAdminData.objects.bulk_create(
        [
            models.NominationAdminData(nomination=nomination, valid_nomination=valid)
            for nomination in nomination_without_admin
        ]
    )


class NominatingMemberFilter(AutocompleteFilter):
    title = "Member"
    field_name = "nominator"
    field = "nominator"
    field_pk = "id"
    parameter_name = "nominator"


class ExtendedNominationAdmin(admin.ModelAdmin):
    model = models.Nomination
    inlines = [NominationAdminDataAdmin]
    autocomplete_fields = ["nominator"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[models.Nomination]:
        return (
            super()
            .get_queryset(request)
            .order_by("nominator", "category", "field_1")
            .select_related("nominator", "category", "admin")
        )

    list_display = ["__str__", "nomination_ip_address", "valid"]
    list_filter = [NominatingMemberFilter, "category"]
    actions = [invalidate_nomination, validate_nomination]

    @admin.display(description="Valid?", boolean=True)
    def valid(self, obj) -> bool:
        try:
            return obj.admin.valid_nomination
        except models.NominationAdminData.DoesNotExist:
            return True


class VotingInformationAdmin(admin.StackedInline):
    model = models.VotingInformation


class ElectionAdmin(admin.ModelAdmin):
    model = models.Election

    def formfield_for_foreignkey(
        self, db_field: ForeignKey, request: HttpRequest, **kwargs: Any
    ) -> ModelChoiceField:
        if db_field.name == "category":
            kwargs["queryset"] = models.Category.objects.filter(election=self.model)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    inlines = [VotingInformationAdmin]


class CategoryAdmin(admin.ModelAdmin):
    model = models.Category

    list_display = ["election", "name", "ballot_position"]
    list_filter = ["election"]

    fieldsets = (
        (
            None,
            {
                "fields": ("election", "name", "description", "nominating_details"),
            },
        ),
        (
            "Ballot configuration",
            {
                "fields": (
                    ("ballot_position", "fields"),
                    "field_1_description",
                    ("field_2_description", "field_2_required"),
                    ("field_3_description", "field_3_required"),
                )
            },
        ),
    )


class FinalistAdmin(admin.ModelAdmin):
    model = models.Finalist

    list_display = ["name", "election", "category", "ballot_position"]
    list_filter = ["category__election"]

    @admin.display()
    def election(self, obj):
        return obj.category.election.name

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.base_fields["category"].label_from_instance = (
            lambda obj: f"{obj} - {obj.election.name}"
        )
        return form

    def get_field_queryset(
        self, db: str | None, db_field: RelatedField, request: HttpRequest
    ) -> QuerySet | None:
        if db_field.name == "category":
            preserved_filters = request.GET.get("_changelist_filters")
            if preserved_filters:
                preserved_filters = parse_qs(preserved_filters)
                if "category__election__id__exact" in preserved_filters:
                    election_id = preserved_filters["category__election__id__exact"][0]
                    filtered_election = models.Election.objects.get(pk=election_id)
                    return models.Category.objects.filter(election=filtered_election)
        return super().get_field_queryset(db, db_field, request)


class ReportRecipientAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            None,
            {
                "fields": ("report_name",),
                "description": mark_safe(
                    markdown.markdown(
                        dedent(
                            """
        The report name must be one of:

        * `nominations`
        """
                        )
                    )
                ),
            },
        ),
        (None, {"fields": ("recipient_email", "recipient_name")}),
    ]

    list_display = ["report_name", "recipient_email", "recipient_name"]


class ReadOnlyUserWidget(forms.TextInput):
    def __init__(self, obj, *args, **kwargs):
        self.obj = obj
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        if self.obj and hasattr(self.obj, "id"):
            user_admin_url = reverse("admin:auth_user_changelist") + str(self.obj.id)
            return mark_safe(f'<a href="{user_admin_url}">{self.obj}</a>')
        else:
            return mark_safe("The user will be created on save.")


class MemberCreationForm(forms.ModelForm):
    class Meta:
        model = models.NominatingMemberProfile
        fields = ["member_number", "preferred_name", "user"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            user = self.instance.user
        except UserModel.DoesNotExist:
            user = None
        self.fields["user"].widget = ReadOnlyUserWidget(user)
        self.fields["user"].required = False

    def save(self, commit: bool = True):
        member = super().save(commit=False)
        try:
            member.user
        except UserModel.DoesNotExist:
            member.user = UserModel.objects.create(
                username=f"manual-{member.member_number}"
            )
            member.user.set_unusable_password()
            if commit:
                member.save()
        return member


class NominatingMemberProfileAdmin(admin.ModelAdmin):
    model = models.NominatingMemberProfile
    form = MemberCreationForm
    list_display = ["member_number", "name", "preferred_name", "created_at"]
    search_fields = ["member_number", "preferred_name"]

    @admin.display()
    def name(self, obj):
        return obj.user.first_name

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return list(self.readonly_fields) + ["member_number"]
        return self.readonly_fields

    def change_view(
        self, request: HttpRequest, object_id, form_url="", extra_context=None
    ) -> HttpResponse:
        extra_context = extra_context or {}
        extra_context["elections"] = models.Election.objects.all()
        return super().change_view(request, object_id, form_url, extra_context)


class NominatingMemberProfileInline(admin.StackedInline):
    model = models.NominatingMemberProfile


class CustomUserAdmin(BaseUserAdmin):
    list_display = list(BaseUserAdmin.list_display) + ["profile_created_at"]
    inlines = [NominatingMemberProfileInline]

    @admin.display(description="Created At")
    def profile_created_at(self, obj):
        if obj is not None:
            return obj.convention_profile.created_at


class RankAdminDataAdmin(admin.StackedInline):
    model = models.RankAdminData


class VotingMemberFilter(AutocompleteFilter):
    title = "Member"
    field_name = "membership"
    field = "membership"
    field_pk = "id"
    parameter_name = "membership"


@admin.action(description="Mark Invalid")
def invalidate_ranking(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
) -> None:
    set_rank_valid(queryset, False)


@admin.action(description="Mark Valid")
def validate_ranking(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
) -> None:
    set_rank_valid(queryset, True)


def set_rank_valid(queryset: QuerySet, validation: bool) -> None:
    models.RankAdminData.objects.filter(rank__in=queryset).update(
        invalidated=not validation
    )

    # find the ones that don't already have info
    without_admin = queryset.exclude(admin__isnull=False)

    # create the missing ones
    models.RankAdminData.objects.bulk_create(
        [
            models.RankAdminData(rank=rank, invalidated=not validation)
            for rank in without_admin
        ]
    )


class RankAdmin(admin.ModelAdmin):
    model = models.Rank
    inlines = [RankAdminDataAdmin]

    list_display = ["finalist", "category", "membership", "rank_date"]
    list_filter = ["finalist__category__election", VotingMemberFilter]
    search_fields = ["finalist__category__name", "membership__member_number"]
    actions = [invalidate_ranking, validate_ranking]

    def get_queryset(self, request: HttpRequest) -> QuerySet[models.Rank]:
        return super().get_queryset(request).select_related("finalist", "membership")

    def category(self, obj):
        return obj.finalist.category


admin.site.unregister(UserModel)
admin.site.register(UserModel, CustomUserAdmin)
admin.site.register(models.Election, ElectionAdmin)
admin.site.register(models.Finalist, FinalistAdmin)
admin.site.register(models.NominatingMemberProfile, NominatingMemberProfileAdmin)
admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Nomination, ExtendedNominationAdmin)
admin.site.register(models.ReportRecipient, ReportRecipientAdmin)
admin.site.register(models.Rank, RankAdmin)
admin.site.register(models.AdminMessage)


# We have some admin views that are using the main site layout, so that we can use the messaging
# framework


@login_required
@user_passes_test_or_forbidden(lambda u: u.is_staff)
@permission_required("nominate.view_raw_results", "nominate.report")
def election_reports(request: HttpRequest, election_id: str) -> HttpResponse:
    election = get_object_or_404(models.Election, slug=election_id)
    return TemplateResponse(
        request,
        "nominate/admin/election_reports.html",
        {
            "is_admin_page": True,
            "election": election,
        },
    )

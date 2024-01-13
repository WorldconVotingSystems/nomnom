from textwrap import dedent
from typing import Any
from urllib.parse import parse_qs

import markdown
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import ForeignKey, QuerySet
from django.db.models.fields.related import RelatedField
from django.forms import ModelChoiceField
from django.http import HttpRequest
from django.utils.safestring import mark_safe

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


class ExtendedNominationAdmin(admin.ModelAdmin):
    model = models.Nomination
    inlines = [NominationAdminDataAdmin]

    list_display = ["__str__", "nomination_ip_address", "valid"]
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
                    "field_2_description",
                    "field_3_description",
                )
            },
        ),
    )


class FinalistAdmin(admin.ModelAdmin):
    model = models.Rank

    list_display = ["description", "election", "category", "ballot_position"]
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


class NominatingMemberProfileAdmin(admin.ModelAdmin):
    model = models.NominatingMemberProfile
    list_display = ["member_number", "name", "preferred_name"]

    @admin.display()
    def name(self, obj):
        return obj.user.first_name


class NominatingMemberProfileInline(admin.StackedInline):
    model = models.NominatingMemberProfile


class CustomUserAdmin(BaseUserAdmin):
    # Define custom features here, for example:
    # list_display, fieldsets, search_fields, etc.
    inlines = [NominatingMemberProfileInline]


admin.site.unregister(UserModel)
admin.site.register(UserModel, CustomUserAdmin)
admin.site.register(models.Election, ElectionAdmin)
admin.site.register(models.Finalist, FinalistAdmin)
admin.site.register(models.NominatingMemberProfile, NominatingMemberProfileAdmin)
admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Nomination, ExtendedNominationAdmin)
admin.site.register(models.ReportRecipient, ReportRecipientAdmin)
admin.site.register(models.Rank)

# Customize the Admin
admin.site.site_title = "NomNom"
admin.site.site_header = "NomNom Administration Interface"
admin.site.index_title = "Hugo Administration"

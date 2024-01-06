from textwrap import dedent
from typing import Any

import markdown
from django.contrib import admin
from django.db.models import ForeignKey
from django.forms import ModelChoiceField
from django.http import HttpRequest
from django.utils.safestring import mark_safe

from . import models


# Yeah, I'm sorry about this name too.
class NominationAdminDataAdmin(admin.StackedInline):
    model = models.NominationAdminData


class ExtendedNominationAdmin(admin.ModelAdmin):
    model = models.Nomination
    inlines = [NominationAdminDataAdmin]


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
                "fields": ("election", "name", "description", "details"),
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
    list_display = ["member_number", "name", "preferred_name"]

    @admin.display()
    def name(self, obj):
        return obj.user.first_name


admin.site.register(models.Election, ElectionAdmin)
admin.site.register(models.Finalist)
admin.site.register(models.NominatingMemberProfile, NominatingMemberProfileAdmin)
admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Nomination, ExtendedNominationAdmin)
admin.site.register(models.ReportRecipient, ReportRecipientAdmin)

from typing import Any

from django.contrib import admin
from django.db.models import ForeignKey
from django.forms import ModelChoiceField
from django.http import HttpRequest

from . import models


# Yeah, I'm sorry about this name too.
class NominationAdminDataAdmin(admin.StackedInline):
    model = models.NominationAdminData


class ExtendedNominationAdmin(admin.ModelAdmin):
    model = models.Nomination
    inlines = [NominationAdminDataAdmin]


class ElectionAdmin(admin.ModelAdmin):
    model = models.Election

    def formfield_for_foreignkey(
        self, db_field: ForeignKey, request: HttpRequest, **kwargs: Any
    ) -> ModelChoiceField:
        if db_field.name == "category":
            kwargs["queryset"] = models.Category.objects.filter(election=self.model)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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


admin.site.register(models.Election, ElectionAdmin)
admin.site.register(models.Finalist)
admin.site.register(models.NominatingMemberProfile)
admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Nomination, ExtendedNominationAdmin)
admin.site.register(models.ReportRecipient)

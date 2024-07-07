from datetime import datetime, timezone
from typing import Any

from django import forms
from django.contrib import admin
from django.http.request import HttpRequest

from . import models


class ProposalForm(forms.ModelForm):
    class Meta:
        model = models.Proposal
        widgets = {
            "full_text": forms.Textarea(attrs={"rows": 50}),
        }
        fields = "__all__"


class VoterTable(admin.TabularInline):
    model = models.Vote
    extra = 0
    fields = ["member_name", "member_email", "vote_cast_at"]
    readonly_fields = ["member_name", "member_email", "vote_cast_at"]

    def has_delete_permission(self, *args, **kwargs) -> bool:
        return False

    def member_name(self, instance: models.Vote) -> str:
        return instance.membership.preferred_name

    def member_email(self, instance: models.Vote) -> str:
        return instance.membership.email

    def vote_cast_at(self, instance: models.Vote) -> str:
        return instance.created


class ProposalAdmin(admin.ModelAdmin):
    model = models.Proposal
    form = ProposalForm
    inlines = [VoterTable]

    list_display = ["name"]
    search_fields = ["title", "description"]

    change_form_template = "admin/advise/proposal/change_form.html"

    fieldsets = [
        (
            None,
            {
                "fields": ["name", "full_text", "can_abstain"],
            },
        ),
        (
            "Admin",
            {
                "fields": ["vote_opens_at", "vote_closes_at"],
            },
        ),
    ]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "start":
            kwargs["initial"] = datetime.now(timezone.utc)

        return super().formfield_for_dbfield(db_field, request, **kwargs)


class VoteAdminDataAdmin(admin.StackedInline):
    model = models.VoteAdminData


class VoteAdmin(admin.ModelAdmin):
    model = models.Vote
    inlines = [VoteAdminDataAdmin]

    def save_model(
        self, request: HttpRequest, obj: models.Vote, form: Any, change: Any
    ) -> None:
        obj.clean()

        return super().save_model(request, obj, form, change)


admin.site.register(models.Proposal, ProposalAdmin)
admin.site.register(models.Vote, VoteAdmin)

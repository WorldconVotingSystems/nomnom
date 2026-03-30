from datetime import datetime, timezone
from typing import Any

from django import forms
from django.contrib import admin
from django.http.request import HttpRequest
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from . import models


class ProposalForm(forms.ModelForm):
    class Meta:
        model = models.Proposal
        widgets = {
            "full_text": forms.Textarea(attrs={"rows": 50}),
        }
        fields = "__all__"


class ProposalAdmin(admin.ModelAdmin):
    model = models.Proposal
    form = ProposalForm

    list_display = ["name", "view_on_site_link"]
    search_fields = ["title", "description"]
    readonly_fields = ["vote_list"]

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
                "fields": ["state"],
            },
        ),
        (
            "Votes",
            {
                "fields": ["vote_list"],
                "description": "Votes are read-only and managed separately.",
            },
        ),
    ]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "start":
            kwargs["initial"] = datetime.now(timezone.utc)

        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def view_on_site_link(self, instance: models.Proposal) -> str:
        url = instance.get_absolute_url()
        return format_html('<a href="{}" target="_blank">View on site</a>', url)

    def vote_list(self, obj):
        if not obj.pk:
            return "(save to see related objects)"

        rows = []
        for c in obj.vote_set.all():
            rows.append(
                f"<tr><td>{c.membership.preferred_name}</td><td>{c.membership.user.email}</td><td>{c.created}</tr>"
            )

        table_content = "\n".join(rows)
        return mark_safe(
            f"<table><tr><th>Name</th><th>Email</th><th>Cast</th></tr>{table_content}</table>"
        )


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

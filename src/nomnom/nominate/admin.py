from textwrap import dedent
from typing import Any
from urllib.parse import parse_qs

import markdown
from admin_auto_filters.filters import AutocompleteFilter
from django import forms
from django.contrib import admin, messages
from django.contrib.admin.models import DELETION, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import ForeignKey, QuerySet
from django.db.models.fields.related import RelatedField
from django.forms import ModelChoiceField
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_admin_action_forms import action_with_form
from django_admin_action_forms.forms import ActionForm

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


def _log_category_action(
    request: HttpRequest, category: models.Category, action_message: str
) -> None:
    """Create an audit log entry for category actions."""
    LogEntry.objects.log_action(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(category).pk,
        object_id=category.pk,
        object_repr=str(category),
        action_flag=DELETION,  # Using DELETION for destructive operations
        change_message=action_message,
    )


class DeleteCategoryForm(ActionForm):
    """Form for confirming category deletion with all related data."""

    confirm = forms.BooleanField(
        required=True,
        label="I understand this will permanently delete this category and all related data",
    )

    class Meta:
        list_objects = True
        help_text = (
            "⚠️ WARNING: This action cannot be undone! "
            "This will permanently delete the selected category and ALL related data including "
            "nominations, finalists, and ranks (votes)."
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add counts to help text dynamically
        if self.queryset.exists():
            category = self.queryset.first()
            nomination_count = models.Nomination.objects.filter(
                category=category
            ).count()
            finalist_count = models.Finalist.objects.filter(category=category).count()
            rank_count = models.Rank.objects.filter(finalist__category=category).count()

            self.opts.help_text = mark_safe(
                f"<strong>⚠️ WARNING: This action cannot be undone!</strong><br><br>"
                f"<strong>Category:</strong> {category.name}<br>"
                f"<strong>Election:</strong> {category.election.name}<br><br>"
                f"<strong>Data to be deleted:</strong><br>"
                f"• Nominations: {nomination_count}<br>"
                f"• Finalists: {finalist_count}<br>"
                f"• Ranks (votes): {rank_count}"
            )


class ResetNominationsForm(ActionForm):
    """Form for confirming nomination reset."""

    confirm = forms.BooleanField(
        required=True,
        label="I understand this will permanently delete all nominations in the selected categories",
    )

    class Meta:
        list_objects = True
        help_text = "This will delete all nominations in the selected categories."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.queryset.exists():
            category_count = self.queryset.count()
            nomination_count = models.Nomination.objects.filter(
                category__in=self.queryset
            ).count()

            if category_count == 1:
                category = self.queryset.first()
                self.opts.help_text = mark_safe(
                    f"<strong>⚠️ WARNING: This action cannot be undone!</strong><br><br>"
                    f"<strong>Category:</strong> {category.name}<br>"
                    f"<strong>Election:</strong> {category.election.name}<br>"
                    f"<strong>Election State:</strong> {category.election.get_state_display()}<br><br>"
                    f"<strong>This operation is only allowed in Pre-Nomination state.</strong><br><br>"
                    f"<strong>Nominations to be deleted:</strong> {nomination_count}"
                )
            else:
                self.opts.help_text = mark_safe(
                    f"<strong>⚠️ WARNING: This action cannot be undone!</strong><br><br>"
                    f"<strong>Categories selected:</strong> {category_count}<br><br>"
                    f"<strong>This operation is only allowed in Pre-Nomination state.</strong><br><br>"
                    f"<strong>Total nominations to be deleted:</strong> {nomination_count}"
                )


class ResetRanksForm(ActionForm):
    """Form for confirming rank reset."""

    confirm = forms.BooleanField(
        required=True,
        label="I understand this will permanently delete all ranks in the selected categories",
    )

    class Meta:
        list_objects = True
        help_text = "This will delete all ranks (votes) in the selected categories."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.queryset.exists():
            category_count = self.queryset.count()
            rank_count = models.Rank.objects.filter(
                finalist__category__in=self.queryset
            ).count()

            if category_count == 1:
                category = self.queryset.first()
                self.opts.help_text = mark_safe(
                    f"<strong>⚠️ WARNING: This action cannot be undone!</strong><br><br>"
                    f"<strong>Category:</strong> {category.name}<br>"
                    f"<strong>Election:</strong> {category.election.name}<br>"
                    f"<strong>Election State:</strong> {category.election.get_state_display()}<br><br>"
                    f"<strong>This operation is only allowed before voting begins "
                    f"(Pre-Nomination through Voting Preview states).</strong><br><br>"
                    f"<strong>Ranks (votes) to be deleted:</strong> {rank_count}"
                )
            else:
                self.opts.help_text = mark_safe(
                    f"<strong>⚠️ WARNING: This action cannot be undone!</strong><br><br>"
                    f"<strong>Categories selected:</strong> {category_count}<br><br>"
                    f"<strong>This operation is only allowed before voting begins "
                    f"(Pre-Nomination through Voting Preview states).</strong><br><br>"
                    f"<strong>Total ranks (votes) to be deleted:</strong> {rank_count}"
                )


# Create the admin actions using the decorator
@action_with_form(
    DeleteCategoryForm,
    description="Delete Category (with all related data)",
)
def delete_category_with_related(modeladmin, request, queryset, data):
    """Delete a category and all related data."""
    if queryset.count() != 1:
        modeladmin.message_user(
            request,
            "Please select exactly one category.",
            level=messages.ERROR,
        )
        return

    category = queryset.first()
    if category is None:
        return

    if not request.user.has_perm("nominate.delete_category"):
        modeladmin.message_user(
            request,
            "You do not have permission to delete categories.",
            level=messages.ERROR,
        )
        return

    category_name = category.name
    category_id = category.id

    # Delete the category (this will cascade to finalists, but we need to handle others)
    with transaction.atomic():
        # Delete ranks first
        deleted_ranks = models.Rank.objects.filter(
            finalist__category=category
        ).delete()[0]

        # Delete nominations
        deleted_nominations = models.Nomination.objects.filter(
            category=category
        ).delete()[0]

        # Delete finalists (will be handled by category deletion cascade)
        deleted_finalists = models.Finalist.objects.filter(category=category).delete()[
            0
        ]

        # Finally, delete the category
        category.delete()

    # Log the action
    action_message = (
        f"Deleted category '{category_name}' (ID: {category_id}) and "
        f"{deleted_nominations} nominations, {deleted_finalists} finalists, "
        f"and {deleted_ranks} ranks"
    )
    _log_category_action(request, category, action_message)

    modeladmin.message_user(
        request,
        f"Successfully deleted category '{category_name}' and {deleted_nominations} nominations, "
        f"{deleted_finalists} finalists, and {deleted_ranks} ranks.",
        level=messages.SUCCESS,
    )


@action_with_form(
    ResetNominationsForm,
    description="Reset Nominations (delete all in category)",
)
def reset_nominations(modeladmin, request, queryset, data):
    """Delete all nominations in selected categories."""
    # Check election state for all categories
    invalid_categories = []
    for category in queryset:
        if category.election.state != models.Election.STATE.PRE_NOMINATION:
            invalid_categories.append(
                f"{category.name} ({category.election.get_state_display()})"
            )

    if invalid_categories:
        modeladmin.message_user(
            request,
            f"Cannot reset nominations: The following categories are not in Pre-Nomination state: "
            f"{', '.join(invalid_categories)}. "
            "Nominations can only be reset in Pre-Nomination state.",
            level=messages.ERROR,
        )
        return

    if not request.user.has_perm("nominate.delete_nomination"):
        modeladmin.message_user(
            request,
            "You do not have permission to delete nominations.",
            level=messages.ERROR,
        )
        return

    # Delete nominations
    with transaction.atomic():
        deleted_count = models.Nomination.objects.filter(
            category__in=queryset
        ).delete()[0]

        # Log the action for each category
        for category in queryset:
            action_message = f"Reset nominations for category '{category.name}'"
            _log_category_action(request, category, action_message)

        category_names = ", ".join([c.name for c in queryset])
        modeladmin.message_user(
            request,
            f"Successfully deleted {deleted_count} nominations from {queryset.count()} "
            f"{'category' if queryset.count() == 1 else 'categories'}: {category_names}.",
            level=messages.SUCCESS,
        )


@action_with_form(
    ResetRanksForm,
    description="Reset Ranks (delete all in category)",
)
def reset_ranks(modeladmin, request, queryset, data):
    """Delete all ranks (votes) in selected categories."""
    # Check election state for all categories - can't reset if voting has started or later
    allowed_states = [
        models.Election.STATE.PRE_NOMINATION,
        models.Election.STATE.NOMINATION_PREVIEW,
        models.Election.STATE.NOMINATIONS_OPEN,
        models.Election.STATE.NOMINATIONS_CLOSED,
        models.Election.STATE.VOTING_PREVIEW,
    ]

    invalid_categories = []
    for category in queryset:
        if category.election.state not in allowed_states:
            invalid_categories.append(
                f"{category.name} ({category.election.get_state_display()})"
            )

    if invalid_categories:
        modeladmin.message_user(
            request,
            f"Cannot reset ranks: The following categories have voting in progress or completed: "
            f"{', '.join(invalid_categories)}. "
            "Ranks can only be reset before voting begins (Pre-Nomination through Voting Preview).",
            level=messages.ERROR,
        )
        return

    if not request.user.has_perm("nominate.delete_rank"):
        modeladmin.message_user(
            request,
            "You do not have permission to delete ranks.",
            level=messages.ERROR,
        )
        return

    # Delete ranks
    with transaction.atomic():
        # deletion here also deletes the related rank admin objects, which means we
        # will report 2x the number of records. So, we query it to get the count right.
        rank_queryset = models.Rank.objects.filter(finalist__category__in=queryset)
        expected_count = rank_queryset.count()

        rank_queryset.delete()

        # Log the action for each category
        for category in queryset:
            action_message = f"Reset ranks for category '{category.name}'"
            _log_category_action(request, category, action_message)

        category_names = ", ".join([c.name for c in queryset])
        modeladmin.message_user(
            request,
            f"Successfully deleted {expected_count} ranks from {queryset.count()} "
            f"{'category' if queryset.count() == 1 else 'categories'}: {category_names}.",
            level=messages.SUCCESS,
        )


class CategoryAdmin(admin.ModelAdmin):
    model = models.Category

    list_display = ["election", "name", "ballot_position"]
    list_filter = ["election"]
    actions = [delete_category_with_related, reset_nominations, reset_ranks]

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

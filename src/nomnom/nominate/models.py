from collections.abc import Iterable
from datetime import UTC, datetime

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext
from django_fsm import FSMField
from markdown import markdown
from pyrankvote import Candidate

from django_svcs.apps import svcs_from
from nomnom.convention import ConventionConfiguration
from nomnom.model_utils import AdminMetadata
from nomnom.nominate.templatetags.nomnom_filters import html_text

UserModel = get_user_model()


class NominatingMemberProfile(models.Model):
    class Meta:
        verbose_name = "Nominating Member Profile"

    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE, related_name="convention_profile"
    )

    preferred_name = models.CharField(max_length=100, null=True)
    member_number = models.CharField(max_length=100, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def display_name(self) -> str:
        if self.preferred_name and self.preferred_name.strip():
            return self.preferred_name

        return self.user.first_name

    def __str__(self):
        return self.display_name

    @receiver(pre_save)
    def set_created_at_on_save(sender, instance, *args, **kwargs):
        if instance.pk is None:
            instance.updated_at = instance.created_at = datetime.now(UTC)


class Election(models.Model):
    class Meta:
        permissions = [
            ("nominate", "Can nominate in WSFS elections"),
            ("preview_nominate", "Can nominate during the preview phase"),
            ("vote", "Can vote in WSFS elections"),
            ("preview_vote", "Can vote in WSFS elections during the preview phase"),
            ("report", "Can access reports for this election"),
        ]

    class STATE:
        PRE_NOMINATION = "pre_nominating"
        NOMINATION_PREVIEW = "nominating_preview"
        NOMINATIONS_OPEN = "nominating"
        NOMINATIONS_CLOSED = "nominating_closed"
        VOTING_PREVIEW = "voting_preview"
        VOTING = "voting"
        VOTING_CLOSED = "voting_closed"

    STATE_CHOICES = (
        (STATE.PRE_NOMINATION, _("Pre-Nomination")),
        (STATE.NOMINATION_PREVIEW, _("Nomination Preview")),
        (STATE.NOMINATIONS_OPEN, _("Nominating")),
        (STATE.NOMINATIONS_CLOSED, _("Nominating Closed")),
        (STATE.VOTING_PREVIEW, _("Voting Preview")),
        (STATE.VOTING, _("Voting")),
        (STATE.VOTING_CLOSED, _("Voting Closed")),
    )

    NOMINATING_STATES = (
        STATE.PRE_NOMINATION,
        STATE.NOMINATION_PREVIEW,
        STATE.NOMINATIONS_OPEN,
    )

    VOTING_STATES = (
        STATE.NOMINATIONS_CLOSED,
        STATE.VOTING_PREVIEW,
        STATE.VOTING,
    )

    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    state = FSMField(default=STATE.PRE_NOMINATION, choices=STATE_CHOICES)

    def __str__(self):
        return self.name

    @property
    def is_nominating(self):
        return (
            self.state == self.STATE.NOMINATIONS_OPEN
            or self.state == self.STATE.NOMINATION_PREVIEW
        )

    @property
    def is_voting(self):
        return self.state in (self.STATE.VOTING, self.STATE.VOTING_PREVIEW)

    def describe_state(self, user: AbstractBaseUser | None = None) -> str:
        if user is None or user.is_anonymous:
            if self.state in self.NOMINATING_STATES:
                return str(_("You must log in to nominate"))

            if self.state in self.VOTING_STATES:
                return str(_("You must log in to vote"))

        match state := self.state:
            case self.STATE.PRE_NOMINATION:
                return str(_("Nominations are not yet open"))

            case self.STATE.NOMINATION_PREVIEW:
                return (
                    str(_("Nominations are previewing"))
                    if self.user_can_nominate(user)
                    else str(_("Nominations are not yet open"))
                )

            case self.STATE.NOMINATIONS_OPEN:
                return str(_("Nominations are open"))

            case self.STATE.VOTING:
                return str(_("Voting is open"))

            case self.STATE.NOMINATIONS_CLOSED:
                return str(_("Nominations are closed"))

            case self.STATE.VOTING_PREVIEW:
                return (
                    str(_("Voting is in Preview"))
                    if self.user_can_vote(user)
                    else str(_("Nominations are closed"))
                )

            case self.STATE.VOTING_CLOSED:
                return str(_("Voting is now closed"))

            case _:
                return f"The election is not configured: {state}"

    @property
    def is_open(self) -> bool:
        return self.is_nominating or self.is_voting

    @property
    def is_preview(self) -> bool:
        return self.state in (self.STATE.VOTING_PREVIEW, self.STATE.NOMINATION_PREVIEW)

    def pretty_state(self, user=None) -> str:
        if self.is_open_for(user):
            return pgettext("election status", "Open")
        return pgettext("election status", "Closed")

    def user_can_nominate(self, user) -> bool:
        if self.state == self.STATE.NOMINATIONS_OPEN:
            return user.has_perm("nominate.nominate") or user.has_perm(
                "nominate.preview_nominate"
            )

        if self.state == self.STATE.NOMINATION_PREVIEW:
            return user.has_perm("nominate.preview_nominate")

        return False

    def nominations_have_closed(self) -> bool:
        return self.state not in [
            self.STATE.PRE_NOMINATION,
            self.STATE.NOMINATIONS_OPEN,
            self.STATE.NOMINATION_PREVIEW,
        ]

    def user_can_vote(self, user) -> bool:
        if self.state == self.STATE.VOTING:
            return user.has_perm("nominate.vote") or user.has_perm(
                "nominate.preview_vote"
            )

        if self.state == self.STATE.VOTING_PREVIEW:
            return user.has_perm("nominate.preview_vote")

        return False

    def is_open_for(self, user):
        if user is None:
            return self.is_open

        return self.user_can_nominate(user) or self.user_can_vote(user)

    @classmethod
    def enrich_with_user_data(
        cls, elections: Iterable["Election"], request: HttpRequest
    ):
        # we only do this if the convention has a packet setting
        convention_configuration = svcs_from(request).get(ConventionConfiguration)

        ElectionPacket = None
        # if the packet application is installed and enabled, let's try load the model here
        if (
            "hugopacket" in settings.INSTALLED_APPS
            and convention_configuration.packet_enabled
        ):
            app_config = apps.get_app_config("hugopacket")
            ElectionPacket = app_config.models_module.ElectionPacket

        user = request.user

        for election in elections:
            election.is_open_for_user = election.is_open_for(user)
            election.user_state = election.describe_state(user=user)
            election.user_pretty_state = election.pretty_state(user=user)

            if ElectionPacket:
                try:
                    packet = ElectionPacket.objects.filter(election=election).first()
                except ElectionPacket.DoesNotExist:
                    packet = None
                election.packet_exists = packet is not None
                election.packet_is_ready = packet and (
                    packet.enabled or request.user.has_perm("hugopacket.preview_packet")
                )
            else:
                election.packet_exists = False

        return elections


class VotingInformation(models.Model):
    election = models.OneToOneField(
        Election, on_delete=models.CASCADE, related_name="voting_info"
    )

    close_date = models.DateTimeField()


class Category(models.Model):
    """The election category"""

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["ballot_position"]

    election = models.ForeignKey(Election, on_delete=models.PROTECT, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    nominating_details = models.TextField(blank=True)
    ballot_position = models.SmallIntegerField()
    fields = models.SmallIntegerField(default=1, choices=[(1, 1), (2, 2), (3, 3)])
    field_1_description = models.CharField(max_length=200)
    field_2_description = models.CharField(max_length=200, null=True, blank=True)
    field_2_required = models.BooleanField(
        default=True,
        null=True,
        help_text="This is only relevant if the field count means it'd be included",
    )
    field_3_description = models.CharField(max_length=200, null=True, blank=True)
    field_3_required = models.BooleanField(
        default=True,
        null=True,
        help_text="This is only relevant if the field count means it'd be included",
    )

    def __str__(self):
        return html_text(markdown(self.name))

    def field_required(self, field_number: int) -> bool:
        if field_number == 1:
            return True

        if field_number == 2:
            return self.field_2_required

        if field_number == 3:
            return self.field_3_required

        return False

    @property
    def field_names(self) -> list[str]:
        return [
            self.field_1_description,
            self.field_2_description,
            self.field_3_description,
        ][: self.fields]


class NominationsManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().prefetch_related("category", "nominator")


class NominationValidManager(NominationsManager):
    def get_queryset(self) -> models.QuerySet:
        return (
            super()
            .get_queryset()
            .filter(Q(admin__valid_nomination=True) | Q(admin__isnull=True))
        )


class Nomination(models.Model):
    class Meta:
        permissions = [
            ("edit_ballot", "Can edit the ballot as an admin"),
        ]

    field_1 = models.CharField(max_length=200)
    field_2 = models.CharField(max_length=200)
    field_3 = models.CharField(max_length=200)

    nominator = models.ForeignKey(
        NominatingMemberProfile, on_delete=models.DO_NOTHING, null=False
    )
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, null=False)

    nomination_date = models.DateTimeField(null=False, auto_now=True)
    nomination_ip_address = models.CharField(max_length=64)

    # this ties the method into canonicalize; ignore it if the canonicalize app
    # is not installed.
    @property
    def work(self):
        canonicalized_nomination = getattr(self, "canonicalizednomination", None)
        if canonicalized_nomination:
            return canonicalized_nomination.work

    def clean(self):
        if self.field_1.strip() or self.field_2.strip() or self.field_3.strip():
            return

        try:
            category = self.category
        except Category.DoesNotExist:
            return

        errors = {
            f"field_{i + 1}": _("must specify at least one field")
            for i in range(category.fields)
        }

        raise ValidationError(errors)

    def field_values(self) -> dict[str, str]:
        field_values = [self.field_1, self.field_2, self.field_3][
            : self.category.fields
        ]
        return dict(zip(self.category.field_names, field_values))

    def pretty_fields(self) -> str:
        fields = [self.field_1, self.field_2, self.field_3][: self.category.fields]
        field_names = [
            self.category.field_1_description,
            self.category.field_2_description,
            self.category.field_3_description,
        ][: self.category.fields]
        return ", ".join([f"{f}: {n}" for f, n in zip(field_names, fields)])

    def proposed_work_name(self) -> str:
        fields = [self.field_1, self.field_2, self.field_3][: self.category.fields]
        return " ".join(fields)

    def canonicalization_display_name(self) -> str:
        fields = [self.field_1, self.field_2, self.field_3][: self.category.fields]
        return " | ".join(fields)

    def __str__(self):
        return f"{self.proposed_work_name()} in {self.category}"

    # make sure we have the objects manager
    objects = NominationsManager()
    valid = NominationValidManager()


class NominationAdminData(models.Model):
    nomination = models.OneToOneField(
        Nomination, on_delete=models.CASCADE, related_name="admin"
    )

    valid_nomination = models.BooleanField(default=True)


class Finalist(models.Model):
    """A Finalist in the Hugo Awards.

    These are not directly linked to nominations, but are instead intented to be manually added by
    the admin. This means that they don't need to have any coupling to the nomination data model.

    """

    class Meta:
        ordering = ["ballot_position"]

    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    name = models.TextField()
    ballot_position = models.SmallIntegerField()
    short_name = models.CharField(
        max_length=120,
        help_text="A short name for display in reports and admin interfaces. Plain text only.",
        default=None,
        null=True,
    )

    def __str__(self):
        return self.short_name if self.short_name else self.name

    def as_candidate(self) -> Candidate:
        return Candidate(html_text(markdown(str(self))))


class ValidManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return (
            super()
            .get_queryset()
            .filter(Q(admin__invalidated=False) | Q(admin__isnull=True))
        )


class Rank(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["membership", "finalist"], name="unique_rank"
            ),
        ]

        permissions = [
            ("edit_ranking_ballot", "Can edit the ranking ballot as an admin"),
            ("view_raw_results", "Can view the raw results as the election proceeds"),
        ]

    membership = models.ForeignKey(
        NominatingMemberProfile, on_delete=models.DO_NOTHING, null=False
    )
    finalist = models.ForeignKey(Finalist, on_delete=models.PROTECT)
    position = models.PositiveSmallIntegerField(null=True, blank=True)
    voter_ip_address = models.CharField(max_length=64, null=True, blank=True)
    rank_date = models.DateTimeField(null=False, auto_now=True)

    # make sure we have the objects manager
    objects = models.Manager()
    valid = ValidManager()


class RankAdminData(AdminMetadata):
    rank = models.OneToOneField(Rank, on_delete=models.CASCADE, related_name="admin")


# These models are configuration models specifically for admin operations.
class ReportRecipient(models.Model):
    report_name = models.CharField(max_length=200)
    recipient_name = models.CharField(max_length=200)
    recipient_email = models.CharField(max_length=200)

    def __str__(self) -> str:
        return f'{self.report_name} to "{self.recipient_name} <{self.recipient_email}>"'


# Admin Messages
class AdminMessage(models.Model):
    message = models.TextField(help_text="Markdown field for the admin message")
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

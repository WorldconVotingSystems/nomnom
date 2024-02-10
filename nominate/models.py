from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import make_aware
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext
from django_fsm import FSMField, transition
from markdown import markdown

from nominate.templatetags.nomnom_filters import html_text

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
            instance.updated_at = instance.created_at = make_aware(datetime.utcnow())


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

    @transition(
        "state",
        source=[STATE.PRE_NOMINATION, STATE.NOMINATIONS_OPEN],
        target=STATE.NOMINATION_PREVIEW,
    )
    def preview_nominations(self):
        ...

    @transition(
        "state",
        source=[STATE.NOMINATION_PREVIEW, STATE.PRE_NOMINATION],
        target=STATE.NOMINATIONS_OPEN,
    )
    def open_nominations(self):
        ...

    @transition("state", source=STATE.NOMINATIONS_OPEN, target=STATE.NOMINATIONS_CLOSED)
    def close_nominations(self):
        ...

    @transition(
        "state",
        source=[STATE.NOMINATIONS_CLOSED, STATE.VOTING],
        target=STATE.VOTING_PREVIEW,
    )
    def preview_voting(self):
        ...

    @transition(
        "state",
        source=[STATE.NOMINATIONS_CLOSED, STATE.VOTING_PREVIEW],
        target=STATE.VOTING,
    )
    def open_voting(self):
        ...

    @transition("stage", source=STATE.VOTING, target=STATE.VOTING_CLOSED)
    def close_voting(self):
        ...

    @property
    def is_nominating(self):
        return self.state == self.STATE.NOMINATIONS_OPEN

    @property
    def is_voting(self):
        return self.state == "voting"

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


class VotingInformation(models.Model):
    election = models.OneToOneField(
        Election, on_delete=models.CASCADE, related_name="voting_info"
    )

    close_date = models.DateTimeField()


class Category(models.Model):
    """The election category"""

    election = models.ForeignKey(Election, on_delete=models.PROTECT, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    nominating_details = models.TextField(blank=True)
    ballot_position = models.SmallIntegerField()
    fields = models.SmallIntegerField(default=1)
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

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["ballot_position"]


class Nomination(models.Model):
    field_1 = models.CharField(max_length=200)
    field_2 = models.CharField(max_length=200)
    field_3 = models.CharField(max_length=200)

    nominator = models.ForeignKey(
        NominatingMemberProfile, on_delete=models.DO_NOTHING, null=False
    )
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, null=False)

    nomination_date = models.DateTimeField(null=False, auto_now=True)
    nomination_ip_address = models.CharField(max_length=64)

    def clean(self):
        if self.field_1.strip() or self.field_2.strip() or self.field_3.strip():
            return

        try:
            category = self.category
        except Category.DoesNotExist:
            return

        errors = {
            f"field_{i+1}": _("must specify at least one field")
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

    def __str__(self):
        return f"{self.category} by {self.nominator.display_name} on {self.nomination_date}"


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

    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    name = models.CharField(max_length=400)
    description = models.TextField()
    ballot_position = models.SmallIntegerField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["ballot_position"]


class Rank(models.Model):
    membership = models.ForeignKey(
        NominatingMemberProfile, on_delete=models.DO_NOTHING, null=False
    )
    finalist = models.ForeignKey(Finalist, on_delete=models.PROTECT)
    position = models.PositiveSmallIntegerField(null=True, blank=True)
    voter_ip_address = models.CharField(max_length=64, null=True, blank=True)


# These models are configuration models specifically for admin operations.
class ReportRecipient(models.Model):
    report_name = models.CharField(max_length=200)
    recipient_name = models.CharField(max_length=200)
    recipient_email = models.CharField(max_length=200)


# Admin Messages
class AdminMessage(models.Model):
    message = models.TextField(help_text="Markdown field for the admin message")
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

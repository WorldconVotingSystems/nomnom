from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django_fsm import FSMField, transition

UserModel = get_user_model()


class NominatingMemberProfile(models.Model):
    class Meta:
        verbose_name = "Nominating Member Profile"

    user = models.OneToOneField(
        UserModel, on_delete=models.DO_NOTHING, related_name="convention_profile"
    )

    preferred_name = models.CharField(max_length=100, null=True)
    member_number = models.CharField(max_length=100, null=True)

    @property
    def display_name(self) -> str:
        if self.preferred_name and self.preferred_name.strip():
            return self.preferred_name

        return self.user.first_name

    def __str__(self):
        return self.user.username


class VotingMember(models.Model):
    user = models.OneToOneField(
        UserModel, on_delete=models.DO_NOTHING, related_name="voter_profile"
    )

    elections = models.ManyToManyField("Election", verbose_name="Participating Votes")

    def __str__(self):
        return self.user.username


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
        (STATE.PRE_NOMINATION, "Pre-Nomination"),
        (STATE.NOMINATION_PREVIEW, "Nomination Preview"),
        (STATE.NOMINATIONS_OPEN, "Nominating"),
        (STATE.NOMINATIONS_CLOSED, "Nominating Closed"),
        (STATE.VOTING_PREVIEW, "Voting Preview"),
        (STATE.VOTING, "Voting"),
        (STATE.VOTING_CLOSED, "Voting Closed"),
    )

    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    state = FSMField(default=STATE.PRE_NOMINATION, choices=STATE_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.state})"

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

    def describe_state(self, user=None) -> str:
        match state := self.state:
            case self.STATE.PRE_NOMINATION:
                return "Nominations are not yet open"

            case self.STATE.NOMINATION_PREVIEW:
                return (
                    "Nominations are previewing"
                    if self.user_can_nominate(user)
                    else "Nominations are not yet open"
                )

            case self.STATE.NOMINATIONS_OPEN:
                return "Nominations are open"

            case self.STATE.VOTING:
                return "Voting is open"

            case self.STATE.NOMINATIONS_CLOSED:
                return "Nominations are closed"

            case self.STATE.VOTING_PREVIEW:
                return (
                    "Voting is in Preview"
                    if self.user_can_vote(user)
                    else "Nominations are closed"
                )

            case self.STATE.VOTING_CLOSED:
                return "Voting is now closed"

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
            return "Open"
        return "Closed"

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


class Category(models.Model):
    """The election category"""

    election = models.ForeignKey(Election, on_delete=models.PROTECT, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    details = models.TextField()
    ballot_position = models.SmallIntegerField()
    fields = models.SmallIntegerField(default=1)
    field_1_description = models.CharField(max_length=100)
    field_2_description = models.CharField(max_length=100, null=True)
    field_3_description = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "categories"


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

        raise ValidationError(
            {
                "field_1": "must specify at least one field",
                "field_2": "must specify at least one field",
                "field_3": "must specify at least one field",
            }
        )

    def __str__(self):
        return f"{self.category} by {self.nominator.display_name} on {self.nomination_date}"


class NominationAdminData(models.Model):
    nomination = models.OneToOneField(
        Nomination, on_delete=models.CASCADE, related_name="admin"
    )

    valid_nomination = models.BooleanField(default=True)


class Finalist(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField()

    def __str__(self):
        return self.description


class Rank(models.Model):
    membership = models.ForeignKey(VotingMember, on_delete=models.PROTECT)
    finalist = models.ForeignKey(Finalist, on_delete=models.PROTECT)
    position = models.PositiveSmallIntegerField()


# These models are configuration models specifically for admin operations.
class ReportRecipient(models.Model):
    report_name = models.CharField(max_length=200)
    recipient_name = models.CharField(max_length=200)
    recipient_email = models.CharField(max_length=200)

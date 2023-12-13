from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
import datetime


UserModel = get_user_model()


class NominatingMember(UserModel):
    elections = models.ManyToManyField(
        "Election", verbose_name="Participating Votes", through="NominationPermission"
    )

    def __str__(self):
        return self.username


class VotingMember(models.Model):
    member_id = models.CharField(max_length=100)
    elections = models.ManyToManyField("Election", verbose_name="Participating Votes")

    def __str__(self):
        return self.member_id


class Election(models.Model):
    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def state_at(self, date_time: datetime.datetime) -> "ElectionState":
        states = (
            self.state_history.filter(
                valid_from__lte=date_time,
            )
            .exclude(valid_to__lte=date_time)
            .order_by("-valid_from")
        )

        if states:
            return states.first().state
        else:
            # Handle the case where there is no state found for the given datetime.
            # This could return the initial state, an error, or however your application needs to handle such cases.
            return ElectionState.State.PRE_NOMINATING  # or raise an exception, etc.


class NominationPermission(models.Model):
    member = models.ForeignKey(NominatingMember, on_delete=models.DO_NOTHING)
    election = models.ForeignKey(Election, on_delete=models.DO_NOTHING)
    nomination_pin = models.CharField(max_length=64)


class ElectionState(models.Model):
    class State(models.TextChoices):
        PRE_NOMINATING = "pre_nomination", _("Not Yet Nominating")
        NOMINATING = "nominating", _("Nominating")
        VOTING = "voting", _("Voting")
        CLOSED = "closed", _("Closed")

    valid_from = models.DateTimeField(null=True, default=None)
    valid_to = models.DateTimeField(null=True, default=None)

    state = models.CharField(choices=State, max_length=20, default=State.PRE_NOMINATING)

    election = models.ForeignKey(
        Election, on_delete=models.PROTECT, related_name="state_history"
    )


def initial_state_for_election(instance: Election, created: bool, raw: bool, **kwargs):
    if raw:
        return

    if not created:
        return

    es = ElectionState(
        valid_from=datetime.datetime.utcnow(),
        valid_to=None,
        state=ElectionState.State.PRE_NOMINATING,
        election=instance,
    )
    es.save()


models.signals.post_save.connect(
    initial_state_for_election,
    sender=Election,
    dispatch_uid="set-initial-election-state",
)


class Category(models.Model):
    """The election category"""

    election = models.ForeignKey(Election, on_delete=models.PROTECT, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    ballot_position = models.SmallIntegerField()
    fields = models.SmallIntegerField(default=1)
    field_1_description = models.CharField(max_length=100)
    field_2_description = models.CharField(max_length=100)
    field_3_description = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "categories"


class Nomination(models.Model):
    field_1 = models.CharField(max_length=200)
    field_2 = models.CharField(max_length=200)
    field_3 = models.CharField(max_length=200)

    nominator = models.ForeignKey(
        NominatingMember, on_delete=models.DO_NOTHING, null=False
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


class Finalist(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField()

    def __str__(self):
        return self.description


class Rank(models.Model):
    membership = models.ForeignKey(VotingMember, on_delete=models.PROTECT)
    finalist = models.ForeignKey(Finalist, on_delete=models.PROTECT)
    position = models.PositiveSmallIntegerField()

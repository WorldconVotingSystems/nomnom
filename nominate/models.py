from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django_fsm import FSMField, transition


UserModel = get_user_model()


class NominatingMemberProfile(models.Model):
    class Meta:
        verbose_name = "Nominating Member Profile"

    user = models.OneToOneField(
        UserModel, on_delete=models.DO_NOTHING, related_name="nominator_profile"
    )
    elections = models.ManyToManyField(
        "Election", verbose_name="Participating Votes", through="NominationPermission"
    )

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
    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    state = FSMField(default="pre_nomination")

    def __str__(self):
        return f"{self.name} ({self.state})"

    @transition(
        "state", source=["pre_nomination", "nominating"], target=["preview_nominating"]
    )
    def preview_nominations(self):
        ...

    @transition("state", source="preview_nominating", target="nominating")
    def open_nominations(self):
        ...

    @transition("state", source="nominating", target="nominatons_closed")
    def close_nominations(self):
        ...

    @transition(
        "state", source=["nominations_closed", "voting"], target="preview_voting"
    )
    def preview_voting(self):
        ...

    @transition("state", source="preview_voting", target="voting")
    def open_voting(self):
        ...

    @transition("stage", source="voting", target="voting_closed")
    def close_voting(self):
        ...


class NominationPermission(models.Model):
    member = models.ForeignKey(NominatingMemberProfile, on_delete=models.DO_NOTHING)
    election = models.ForeignKey(Election, on_delete=models.DO_NOTHING)
    nomination_pin = models.CharField(max_length=64)


class Category(models.Model):
    """The election category"""

    election = models.ForeignKey(Election, on_delete=models.PROTECT, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
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


class Finalist(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField()

    def __str__(self):
        return self.description


class Rank(models.Model):
    membership = models.ForeignKey(VotingMember, on_delete=models.PROTECT)
    finalist = models.ForeignKey(Finalist, on_delete=models.PROTECT)
    position = models.PositiveSmallIntegerField()

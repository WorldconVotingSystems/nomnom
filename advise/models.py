# Create your models here.

from datetime import datetime, timezone

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone as django_utils_timezone
from django.utils.translation import gettext_lazy as _
from markdownfield.models import MarkdownField, RenderedMarkdownField
from markdownfield.validators import VALIDATOR_STANDARD
from model_utils.models import TimeStampedModel

from nominate.models import NominatingMemberProfile
from nomnom.model_utils import AdminMetadata


class IsOpenManager(models.Manager):
    def __init__(self):
        super().__init__()
        self.when = datetime.now(timezone.utc)

    def at(self, when: datetime):
        self.when = when
        return self

    def get_queryset(self) -> models.QuerySet:
        qs = super().get_queryset()
        qs = qs.filter(
            (
                models.Q(vote_opens_at__lte=self.when)
                | models.Q(vote_opens_at__isnull=True)
            )
            & (
                models.Q(vote_closes_at__gte=self.when)
                | models.Q(vote_closes_at__isnull=True)
            )
        )
        return qs


class Proposal(models.Model):
    name = models.CharField()
    full_text = MarkdownField(
        validator=VALIDATOR_STANDARD, rendered_field="rendered_full_text"
    )
    rendered_full_text = RenderedMarkdownField()
    vote_opens_at = models.DateTimeField(
        default=django_utils_timezone.now, null=False, blank=False
    )
    vote_closes_at = models.DateTimeField(null=True, blank=True)

    can_abstain = models.BooleanField(default=False)

    def total_votes(self, include_invalid: bool = False) -> int:
        return self.votes_for_count(include_invalid).count()

    def invalid_votes(self) -> int:
        return VoteAdminData.objects.filter(
            vote__proposal=self, invalidated=True
        ).count()

    def yes_votes(self, include_invalid: bool = False) -> int:
        return (
            self.votes_for_count(include_invalid)
            .filter(selection=Vote.Selection.YES)
            .count()
        )

    def no_votes(self, include_invalid: bool = False) -> int:
        return (
            self.votes_for_count(include_invalid)
            .filter(selection=Vote.Selection.NO)
            .count()
        )

    def abstentions(self, include_invalid: bool = False) -> int:
        return (
            self.votes_for_count(include_invalid)
            .filter(selection=Vote.Selection.ABSTAIN)
            .count()
        )

    def votes_for_count(self, include_invalid: bool) -> models.QuerySet:
        return (
            self.all_votes_query_set if include_invalid else self.valid_vote_query_set
        )

    @property
    def valid_vote_query_set(self) -> models.QuerySet:
        return Vote.objects.filter(proposal=self, voteadmindata__invalidated=False)

    @property
    def all_votes_query_set(self) -> models.QuerySet:
        return Vote.objects.filter(proposal=self)

    def __str__(self) -> str:
        return self.name

    # make sure we have the objects manager
    objects = models.Manager()
    open = IsOpenManager()


class Vote(TimeStampedModel, models.Model):
    class Selection(models.TextChoices):
        YES = "yes", _("Yes")
        NO = "no", _("No")
        ABSTAIN = "abstain", _("Abstain")

    membership = models.ForeignKey(NominatingMemberProfile, on_delete=models.CASCADE)
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    selection = models.CharField(choices=Selection, max_length=7)

    @property
    def can_abstain(self):
        return self.vote.can_abstain

    def clean(self) -> None:
        if self.selection == self.Selection.ABSTAIN and not self.can_abstain:
            raise ValidationError(
                {"selection": _("This vote does not allow abstentions.")}
            )

    def __str__(self) -> str:
        return f"{self.membership}: {self.selection}"


class VoteAdminData(AdminMetadata):
    vote = models.OneToOneField(Vote, on_delete=models.CASCADE)

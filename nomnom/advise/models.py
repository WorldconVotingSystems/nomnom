# Create your models here.


from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField
from markdownfield.models import MarkdownField, RenderedMarkdownField
from markdownfield.validators import VALIDATOR_STANDARD
from model_utils.models import TimeStampedModel

from nomnom.nominate.models import NominatingMemberProfile
from nomnom.model_utils import AdminMetadata


class IsOpenManager(models.Manager):
    def __init__(self, allow_preview: bool = False):
        super().__init__()
        self.allow_preview = allow_preview

    def get_queryset(self) -> models.QuerySet:
        qs = super().get_queryset()
        if self.allow_preview:
            open_states = [Proposal.STATE.PREVIEW, Proposal.STATE.OPEN]
        else:
            open_states = [Proposal.STATE.OPEN]
        qs = qs.filter(state__in=open_states)
        return qs


class Proposal(models.Model):
    class Meta:
        permissions = [
            ("can_preview", "Can preview proposals"),
        ]

    class STATE:
        PREVIEW = "preview"
        OPEN = "open"
        CLOSED = "closed"

    STATE_CHOICES = (
        (STATE.PREVIEW, _("Previewing")),
        (STATE.OPEN, _("Open")),
        (STATE.CLOSED, _("Closed")),
    )

    name = models.CharField()
    full_text = MarkdownField(
        validator=VALIDATOR_STANDARD, rendered_field="rendered_full_text"
    )
    rendered_full_text = RenderedMarkdownField()
    state = FSMField(default=STATE.PREVIEW, choices=STATE_CHOICES)

    def get_absolute_url(self):
        return reverse("advise:vote", kwargs={"pk": self.id})

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

    @property
    def state_name(self) -> str:
        return dict(self.STATE_CHOICES)[self.state]

    @classmethod
    def is_open_for_user(cls, request, *args, **kwargs) -> bool:
        if request.user.has_perm("advise.can_preview"):
            proposal = cls.objects.get(pk=kwargs["pk"])
        else:
            try:
                proposal = cls.open.get(pk=kwargs["pk"])
            except cls.DoesNotExist:
                return False

        return proposal is not None

    # make sure we have the objects manager
    objects = models.Manager()
    open = IsOpenManager()
    previewing = IsOpenManager(allow_preview=True)


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

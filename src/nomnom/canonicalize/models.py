import typing

from django.core.exceptions import ValidationError
from django.db import models

from nomnom.nominate.models import Nomination

if typing.TYPE_CHECKING:
    from nomnom.nominate import models as nominate


# the Work can reference the nominate app's models. The other direction is
# not okay.
#
# Works do not have the multiple field format of the nominate app's Nomination; they are a
# plain text field, since they're not actually for display or member-facing.
class Work(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey("nominate.Category", on_delete=models.PROTECT)
    notes = models.TextField(blank=True)

    nominations = models.ManyToManyField(
        "nominate.Nomination", through="CanonicalizedNomination"
    )

    @property
    def election(self) -> "nominate.Election":
        return self.category.election

    def __str__(self) -> str:
        return self.name


class CanonicalizedNomination(models.Model):
    """Associate works with nominations.

    This is a many-to-many relationship, but we only allow nominations in this to appear once."""

    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    nomination = models.OneToOneField("nominate.Nomination", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["work", "nomination"], name="unique_work_nomination"
            ),
            # no nomination can appear more than once in this relation.
            models.UniqueConstraint(fields=["nomination"], name="unique_nomination"),
        ]


class CategoryBallot(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "nominator"], name="unique_nominator_category"
            )
        ]

    category = models.ForeignKey("nominate.Category", on_delete=models.CASCADE)
    nominator = models.ForeignKey(
        "nominate.NominatingMemberProfile", on_delete=models.CASCADE
    )

    # this is a hack, but it's probably valid for a while. Changing this will absolutely
    # need code changes, but it's not likely to happen soon.
    work_1 = models.ForeignKey(Work, on_delete=models.PROTECT, related_name="+")
    work_2 = models.ForeignKey(
        Work, on_delete=models.PROTECT, related_name="+", null=True
    )
    work_3 = models.ForeignKey(
        Work, on_delete=models.PROTECT, related_name="+", null=True
    )
    work_4 = models.ForeignKey(
        Work, on_delete=models.PROTECT, related_name="+", null=True
    )
    work_5 = models.ForeignKey(
        Work, on_delete=models.PROTECT, related_name="+", null=True
    )

    def clean_fields(self, exclude=None):
        try:
            super().clean_fields(exclude)
            errors = {}
        except ValidationError as e:
            errors = e.error_dict

        works = [self.work_1, self.work_2, self.work_3, self.work_4, self.work_5]
        for i, work in enumerate(works):
            if work is None:
                continue

            if work.category != self.category:
                errors[f"work_{i + 1}"] = [
                    "This work is not in the category for this ballot."
                ]

        if errors:
            raise ValidationError(errors)

    def to_csv_row(self) -> list[str]:
        return [
            self.nominator.member_number,
            self.category.name,
            self.work_1.name if self.work_1 else "",
            self.work_2.name if self.work_2 else "",
            self.work_3.name if self.work_3 else "",
            self.work_4.name if self.work_4 else "",
            self.work_5.name if self.work_5 else "",
        ]

    def __str__(self) -> str:
        return f"{self.nominator} - {self.category}"

    def __rich_repr__(self):
        yield self.category
        yield self.nominator.member_number
        yield self.work_1
        if self.work_2 is not None:
            yield self.work_2
        if self.work_3 is not None:
            yield self.work_3
        if self.work_4 is not None:
            yield self.work_4
        if self.work_5 is not None:
            yield self.work_5

    @classmethod
    def from_nominations(
        cls,
        nominator: "nominate.NominatingMemberProfile",
        category: "nominate.Nomination",
        create: bool = False,
    ) -> "CategoryBallot":
        # create a category ballot by querying across the nominations to the Work.
        nominations = Nomination.valid.filter(category=category, nominator=nominator)
        works = Work.objects.filter(nominations__in=nominations)
        # pad works up to 5
        if len(works) < 5:
            works += [None] * (5 - len(works))

        if create:
            return cls.objects.create(
                category=category,
                nominator=nominator,
                work_1=works[0],
                work_2=works[1],
                work_3=works[2],
                work_4=works[3],
                work_5=works[4],
            )

        else:
            return cls(
                category=category,
                nominator=nominator,
                work_1=works[0],
                work_2=works[1],
                work_3=works[2],
                work_4=works[3],
                work_5=works[4],
            )

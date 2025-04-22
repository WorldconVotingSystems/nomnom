from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q, Value
from django.db.models.functions import Concat, Lower
from django.db.models.signals import post_save
from django.dispatch import receiver

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
        "nominate.Nomination", through="CanonicalizedNomination", related_name="works"
    )

    @property
    def election(self) -> "nominate.Election":
        return self.category.election

    def __str__(self) -> str:
        return self.name

    @classmethod
    def find_match_based_on_identical_nomination(
        cls, name: str, category: "nominate.Category"
    ) -> "Work | None":
        field_count = category.fields
        if field_count == 1:
            combined_name = Lower(F("nominations__field_1"))
        elif field_count == 2:
            combined_name = Lower(
                Concat(
                    "nominations__field_1",
                    Value(" "),
                    "nominations__field_2",
                )
            )
        elif field_count == 3:
            combined_name = Lower(
                Concat(
                    "nominations__field_1",
                    Value(" "),
                    "nominations__field_2",
                    Value(" "),
                    "nominations__field_3",
                )
            )
        else:
            raise ValueError("Unsupported field count")
        query = (
            cls.objects.filter(category=category)
            .annotate(combined_name=combined_name, work_name=Lower(F("name")))
            .filter(Q(combined_name=name.lower()) | Q(work_name=name.lower()))
        )
        return query.first()

    def combine_works(self, other_works) -> None:
        """Combine this work with other works.

        This will associate all nominations from the other works with this work, and then delete the other works.
        """
        for other_work in other_works:
            # Get nominations associated with the other work
            nominations_to_transfer = list(other_work.nominations.all())

            # Remove the existing Many-to-Many relationship
            other_work.nominations.clear()

            # Add the nominations to 'self' but avoid duplicates
            for nomination in nominations_to_transfer:
                if not self.nominations.filter(pk=nomination.pk).exists():
                    self.nominations.add(nomination)

            # Finally, delete the other work entry
            other_work.delete()


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


@receiver(post_save, sender=nominate.Nomination)
def link_work_to_nomination(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.work is not None:
        return

    work = Work.find_match_based_on_identical_nomination(
        instance.proposed_work_name(), instance.category
    )

    if work is not None:
        work.nominations.add(instance)
        work.save()


def remove_canonicalization(
    nominations: models.QuerySet["nominate.Nomination"],
) -> None:
    """Remove canonicalization for a set of nominations.

    This is a destructive operation; it will remove the association between the nominations and the Work.
    """
    CanonicalizedNomination.objects.filter(nomination__in=nominations).delete()


def group_nominations(nominations: models.QuerySet, work: Work | None) -> Work:
    """Group a set of nominations into a single Work.

    The outcome of this is that every nomination in the group will be
    associated with the single work referenced in the invocation.
    """
    # two things to consider here:
    #
    # 1. We will associate both invalid and valid nominations; even if the admin has invalidated a nomination, we want it to be associated with the Work.
    # 2. If we get a request for a nomination that doesn't exist, we need to respond with an error; that's an indication that something is wrong.

    # if we have a work, we are going to attempt to associate the nominations with that work.

    # if any of those nominations are already associated with a work, we need to remove them from that work, as
    # we are assigning them to an existing one.
    if work is not None:
        for nomination in nominations:
            if nomination.work is not None:
                nomination.work.nominations.remove(nomination)

    else:
        works = set()
        for nomination in nominations:
            if nomination.work is not None:
                works.add(nomination.work)

        if len(set(works)) > 1:
            raise ValidationError(
                "You cannot associate nominations with multiple works."
            )

        if set(works):
            work = works.pop()

        else:
            work = Work.objects.create(
                name=nominations.first().proposed_work_name(),
                category=nominations.first().category,
            )

    work.nominations.add(*nominations)

    return work

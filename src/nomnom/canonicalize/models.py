import typing

from django.db import models

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
            models.UniqueConstraint(fields=["nomination"], name="unique_nomination"),
        ]

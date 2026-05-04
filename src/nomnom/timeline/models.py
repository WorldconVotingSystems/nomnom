from django.db import models


class TimelineEvent(models.Model):
    class Meta:
        ordering = ["position"]

    label = models.CharField(max_length=255)
    date = models.CharField(
        max_length=255,
        help_text="e.g. 'Feb 12th 2026' or 'Early May 2026'.",
    )
    position = models.PositiveSmallIntegerField(default=0)
    provisional = models.BooleanField(
        default=False,
        help_text="Whether to show a caveat about the date being provisional.",
    )
    complete = models.BooleanField(
        default=False,
        help_text="Whether the event has passed.",
    )

    def __str__(self) -> str:
        return self.label

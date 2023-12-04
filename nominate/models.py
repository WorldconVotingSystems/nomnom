from django.core.exceptions import ValidationError
from django.db import models


class Entry(models.Model):
    field_1 = models.CharField(max_length=200)
    field_2 = models.CharField(max_length=200)
    field_3 = models.CharField(max_length=200)

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

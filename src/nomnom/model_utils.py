from django.db import models


class AdminMetadata(models.Model):
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    invalidated = models.BooleanField(default=False)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

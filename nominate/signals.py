from django.conf import settings
from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from nominate import admin
from nominate.models import NominatingMemberProfile, Nomination


@receiver(m2m_changed, sender=Group.user_set.through)
def user_added_or_removed_from_group(sender, instance, action, pk_set, **kwargs):
    if action == "post_remove":
        try:
            instance.convention_profile
        except NominatingMemberProfile.DoesNotExist:
            # no member for this, so we don't have nominations to remove
            return

        groups = Group.objects.filter(pk__in=pk_set)
        if any(g.name == settings.NOMNOM_NOMINATING_GROUP for g in groups):
            # we've removed the user from the nominating group; we are going to invalidate all the
            # user's nominations now.
            admin.set_validation(
                Nomination.objects.filter(nominator=instance.convention_profile), False
            )

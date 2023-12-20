import re
from typing import Any
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from social_core.strategy import BaseStrategy

from nominate.models import NominatingMemberProfile

UserModel = get_user_model()


def set_user_wsfs_membership(
    strategy: BaseStrategy, details: dict[str, Any], user=UserModel, *args, **kwargs
) -> None:
    if not user:
        return

    changed = False

    wsfs_status_key = strategy.setting("WSFS_STATUS_KEY", default="wsfs_status")
    nominate_pattern_str = strategy.setting("WSFS_STATUS_NOMINATE_PATTERN", "Nominate")
    nominate_pattern = re.compile(nominate_pattern_str)

    if nominate_pattern.search(details[wsfs_status_key]) is not None:
        group = Group.objects.get(
            name=strategy.setting("NOMINATING_GROUP", default="Nominator")
        )
        changed = group.user_set.add(user)

        nmp, created = NominatingMemberProfile.objects.get_or_create(user=user)
        changed = changed or created

    if changed:
        strategy.storage.user.changed(user)

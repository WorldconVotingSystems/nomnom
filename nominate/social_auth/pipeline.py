import re
from typing import Any
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from social_core.strategy import BaseStrategy

from nominate.models import NominatingMemberProfile

UserModel = get_user_model()


def get_wsfs_permissions(
    strategy: BaseStrategy,
    details: dict[str, Any],
    user=UserModel,
    *args,
    **kwargs,
) -> None:
    wsfs_status_key = strategy.setting("WSFS_STATUS_KEY", default="wsfs_status")
    nominate_pattern_str = strategy.setting("WSFS_STATUS_NOMINATE_PATTERN", "Nominate")
    nominate_pattern = re.compile(nominate_pattern_str)
    vote_pattern_str = strategy.setting("WSFS_STATUS_VOTE_PATTERN", "Vote")
    vote_pattern = re.compile(vote_pattern_str)

    if wsfs_status_key not in details:
        return

    details["can_nominate"] = (
        nominate_pattern.search(details[wsfs_status_key]) is not None
    )
    details["can_vote"] = vote_pattern.search(details[wsfs_status_key]) is not None


def set_user_wsfs_membership(
    strategy: BaseStrategy, details: dict[str, Any], user=UserModel, *args, **kwargs
) -> None:
    if not user:
        return

    changed = False

    wsfs_status_key = strategy.setting("WSFS_STATUS_KEY", default="wsfs_status")

    if wsfs_status_key in details:
        # there is a WSFS user; we create a profile for them
        nmp, created = NominatingMemberProfile.objects.get_or_create(user=user)
        changed = changed or created
        if created and details.get("preferred_name"):
            nmp.preferred_name = details["preferred_name"]

    if changed:
        strategy.storage.user.changed(user)


def add_election_permissions(
    strategy: BaseStrategy, details: dict[str, Any], user=UserModel, *args, **kwargs
) -> None:
    if user is None:
        return

    changed = False

    if details.get("can_nominate", False):
        group = Group.objects.get(
            name=strategy.setting("NOMINATING_GROUP", default="Nominator")
        )
        changed = changed or group.user_set.add(user)

    if details.get("can_vote", False):
        group = Group.objects.get(
            name=strategy.setting("NOMINATING_GROUP", default="Voter")
        )
        changed = changed or group.user_set.add(user)

    if changed:
        strategy.storage.user.changed(user)

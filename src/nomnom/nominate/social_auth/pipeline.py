import re
from datetime import datetime
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django_svcs.apps import svcs_from
from social_core.exceptions import AuthException
from social_core.strategy import BaseStrategy

from nomnom.convention import ConventionConfiguration
from nomnom.nominate.models import NominatingMemberProfile

UserModel = get_user_model()


class IncompleteRegistration(AuthException):
    def __init__(self, backend, parameters: list[str], *args, **kwargs):
        self.parameters = parameters
        super().__init__(backend, *args, **kwargs)

    def __str__(self):
        return (
            f"The user details was missing required values: {','.join(self.parameters)}"
        )


def get_wsfs_permissions(
    strategy: BaseStrategy,
    details: dict[str, Any],
    user=UserModel,
    *args,
    **kwargs,
) -> None:
    wsfs_status_key: str = cast(
        str, strategy.setting("WSFS_STATUS_KEY", default="wsfs_status")
    )
    nominate_pattern_str: str = cast(
        str, strategy.setting("WSFS_STATUS_NOMINATE_PATTERN", "Nominate")
    )
    nominate_pattern = re.compile(nominate_pattern_str)
    vote_pattern_str: str = cast(
        str, strategy.setting("WSFS_STATUS_VOTE_PATTERN", "Vote")
    )
    vote_pattern = re.compile(vote_pattern_str)

    if wsfs_status_key not in details or not details[wsfs_status_key]:
        raise IncompleteRegistration(kwargs["backend"], parameters=["wsfs_status_key"])

    details["can_nominate"] = (
        nominate_pattern.search(details[wsfs_status_key]) is not None
    )
    details["can_vote"] = vote_pattern.search(details[wsfs_status_key]) is not None


def restrict_wsfs_permissions_by_date(
    strategy: BaseStrategy,
    details: dict[str, Any],
    user=UserModel,
    *args,
    **kwargs,
):
    convention_configuration = svcs_from(strategy.request).get(ConventionConfiguration)

    if convention_configuration.nomination_eligibility_cutoff is not None:
        date_added = details["date_added"]
        if details["can_nominate"]:
            details["can_nominate"] = (
                date_added < convention_configuration.nomination_eligibility_cutoff
            )


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
        if created:
            preferred_name_maybe = details.get("preferred_name")
            if not preferred_name_maybe:
                preferred_name_maybe = details.get("full_name")

            if preferred_name_maybe and nmp.preferred_name != preferred_name_maybe:
                nmp.preferred_name = preferred_name_maybe
                changed = True
            if details.get("ticket_number") and nmp.member_number != str(
                details["ticket_number"]
            ):
                nmp.member_number = str(details["ticket_number"])
                changed = True

            if changed:
                nmp.save()

    else:
        raise IncompleteRegistration(kwargs["backend"], parameters=["wsfs_status_key"])

    if changed:
        strategy.storage.user.changed(user)


def normalize_date_fields(
    strategy: BaseStrategy, details: dict[str, Any], user=UserModel, *args, **kwargs
) -> None:
    for field in ["date_added", "date_updated"]:
        if field in details:
            details[field] = datetime.fromisoformat(details[field])


def add_election_permissions(
    strategy: BaseStrategy, details: dict[str, Any], user=UserModel, *args, **kwargs
) -> None:
    if user is None:
        return

    changed = False
    convention = svcs_from(strategy.request).get(ConventionConfiguration)

    if details.get("can_nominate", False):
        group = Group.objects.get(name=convention.nominating_group)
        changed = changed or group.user_set.add(user)

    if details.get("can_vote", False):
        group = Group.objects.get(name=convention.voting_group)
        changed = changed or group.user_set.add(user)

    if changed:
        strategy.storage.user.changed(user)

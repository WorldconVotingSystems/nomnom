from collections.abc import Callable
from datetime import datetime
from typing import Any

import pytest
from django.contrib.auth.models import Group

from nomnom.nominate.models import NominatingMemberProfile
from nomnom.nominate.social_auth.pipeline import (
    IncompleteRegistration,
    add_election_permissions,
    get_wsfs_permissions,
    normalize_date_fields,
    restrict_wsfs_permissions_by_date,
    set_user_wsfs_membership,
)


@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(username="testuser", password="12345")


@pytest.fixture
def group(db):
    return Group.objects.create(name="Nominator")


@pytest.fixture
def pipeline_run(social_core_strategy, user):
    def runner(pipeline: list[Callable], details: dict[str, Any]):
        for func in pipeline:
            func(social_core_strategy, details, user, backend="test")

    return runner


@pytest.mark.django_db
def test_get_wsfs_permissions(social_core_strategy):
    details = {"wsfs_status": "Can Nominate, Can Vote"}
    get_wsfs_permissions(social_core_strategy, details, backend="test")
    assert details["can_nominate"]
    assert details["can_vote"]


def test_handle_missing_wsfs_permissions(social_core_strategy):
    details = {}
    with pytest.raises(IncompleteRegistration):
        get_wsfs_permissions(social_core_strategy, details, backend="test")
    assert "can_nominate" not in details
    assert "can_vote" not in details


@pytest.mark.django_db
def test_set_user_wsfs_membership(social_core_strategy, user):
    details = {
        "preferred_name": "Preferred User",
        "ticket_number": "1234567890",
        "wsfs_status": "Can Nominate",
    }
    set_user_wsfs_membership(social_core_strategy, details, user, backend="test")

    nmp = NominatingMemberProfile.objects.get(user=user)
    assert nmp.preferred_name == "Preferred User"
    assert nmp.member_number == "1234567890"


@pytest.mark.django_db
def test_add_election_permissions(
    social_core_strategy, user, group, social_core_settings
):
    details = {"can_nominate": True}

    social_core_settings["NOMINATING_GROUP"] = group.name
    add_election_permissions(social_core_strategy, details, user, backend="test")

    user.refresh_from_db()
    assert group in user.groups.all()


@pytest.mark.django_db
def test_add_election_permissions_no_permissions(
    social_core_strategy, user, group, social_core_settings
):
    details = {"can_nominate": False}

    social_core_settings["NOMINATING_GROUP"] = group.name
    add_election_permissions(social_core_strategy, details, user, backend="test")

    user.refresh_from_db()
    assert group not in user.groups.all()


def test_normalize_date_fields_with_valid_dates(
    social_core_strategy, user, group, social_core_settings
):
    details = {
        "date_added": "2024-01-29T22:35:42.000000Z",
        "date_updated": "2024-01-29T22:47:09.000000Z",
    }

    normalize_date_fields(social_core_strategy, details, user)

    assert isinstance(details["date_added"], datetime), (
        "date_added is not a datetime instance"
    )
    assert isinstance(details["date_updated"], datetime), (
        "date_updated is not a datetime instance"
    )


def test_normalize_date_fields_missing_one_date(
    social_core_strategy, user, group, social_core_settings
):
    details = {"date_added": "2024-01-29T22:35:42.000000Z"}

    normalize_date_fields(social_core_strategy, details, user)

    assert isinstance(details["date_added"], datetime), (
        "date_added is not a datetime instance"
    )

    with pytest.raises(KeyError):
        # This should raise a KeyError as 'date_updated' does not exist
        details["date_updated"]


def test_normalize_date_fields_with_invalid_date_format(
    social_core_strategy, user, group, social_core_settings
):
    details = {"date_added": "wrong format date"}

    with pytest.raises(ValueError):
        normalize_date_fields(social_core_strategy, details, user)


def test_normalize_date_fields_with_no_date_fields(
    social_core_strategy, user, group, social_core_settings
):
    details = {"username": "clyde-10814"}

    normalize_date_fields(social_core_strategy, details, user)

    assert "date_added" not in details, "date_added should not be in details"
    assert "date_updated" not in details, "date_updated should not be in details"


@pytest.mark.django_db
def test_pipeline_for_new_user_before_cutoff(pipeline_run):
    Group.objects.create(name="Nominator")
    Group.objects.create(name="Voter")

    details = {
        "preferred_name": "Preferred User",
        "ticket_number": "1234567890",
        "wsfs_status": "Nominate and Vote",
        "date_added": "2024-01-29T22:35:42.000000Z",
        "date_updated": "2024-01-29T22:47:09.000000Z",
    }

    pipeline = [
        get_wsfs_permissions,
        set_user_wsfs_membership,
        normalize_date_fields,
        restrict_wsfs_permissions_by_date,
        add_election_permissions,
    ]

    pipeline_run(pipeline, details)

    assert details["can_nominate"]
    assert details["can_vote"]

    nmp = NominatingMemberProfile.objects.get(user__username="testuser")
    assert nmp.preferred_name == "Preferred User"
    assert nmp.member_number == "1234567890"

    group_names = [g.name for g in nmp.user.groups.all()]
    assert "Nominator" in group_names
    assert "Voter" in group_names


@pytest.mark.django_db
def test_pipeline_for_new_user_after_cutoff(pipeline_run):
    Group.objects.create(name="Nominator")
    Group.objects.create(name="Voter")

    details = {
        "preferred_name": "Preferred User",
        "ticket_number": "1234567890",
        "wsfs_status": "Nominate and Vote",
        "date_added": "2024-02-25T22:35:42.000000Z",
    }

    pipeline = [
        get_wsfs_permissions,
        set_user_wsfs_membership,
        normalize_date_fields,
        restrict_wsfs_permissions_by_date,
        add_election_permissions,
    ]

    pipeline_run(pipeline, details)

    assert not details["can_nominate"]
    assert details["can_vote"]

    nmp = NominatingMemberProfile.objects.get(user__username="testuser")
    assert nmp.preferred_name == "Preferred User"
    assert nmp.member_number == "1234567890"

    group_names = [g.name for g in nmp.user.groups.all()]
    assert "Nominator" not in group_names
    assert "Voter" in group_names

import pytest
from django.contrib.auth.models import Group

from nominate.models import NominatingMemberProfile
from nominate.social_auth.pipeline import (
    add_election_permissions,
    get_wsfs_permissions,
    set_user_wsfs_membership,
)


@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(username="testuser", password="12345")


@pytest.fixture
def group(db):
    return Group.objects.create(name="Nominator")


@pytest.mark.django_db
def test_get_wsfs_permissions(social_core_strategy):
    details = {"wsfs_status": "Can Nominate, Can Vote"}
    get_wsfs_permissions(social_core_strategy, details)
    assert details["can_nominate"]
    assert details["can_vote"]


@pytest.mark.django_db
def test_set_user_wsfs_membership(social_core_strategy, user):
    details = {
        "preferred_name": "Preferred User",
        "ticket_number": "1234567890",
        "wsfs_status": "Can Nominate",
    }
    set_user_wsfs_membership(social_core_strategy, details, user)

    nmp = NominatingMemberProfile.objects.get(user=user)
    assert nmp.preferred_name == "Preferred User"
    assert nmp.member_number == "1234567890"


@pytest.mark.django_db
def test_add_election_permissions(
    social_core_strategy, user, group, social_core_settings
):
    details = {"can_nominate": True}

    social_core_settings["NOMINATING_GROUP"] = group.name
    add_election_permissions(social_core_strategy, details, user)

    user.refresh_from_db()
    assert group in user.groups.all()

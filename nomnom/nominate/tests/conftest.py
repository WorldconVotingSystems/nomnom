import pytest
from django.contrib.auth.models import Permission
from django.test import RequestFactory
from nomnom.nominate import factories


@pytest.fixture(name="member")
def make_member(voting_user):
    return factories.NominatingMemberProfileFactory.create(user=voting_user)


@pytest.fixture(name="voting_user")
def make_user():
    user = factories.UserFactory.create()
    user.user_permissions.add(
        Permission.objects.get(codename="vote", content_type__app_label="nominate")
    )
    return user


@pytest.fixture(name="staff_user")
def make_staff_user():
    return factories.UserFactory.create(is_staff=True)


@pytest.fixture(name="staff")
def make_staff(staff_user):
    return factories.NominatingMemberProfileFactory(user=staff_user)


@pytest.fixture(name="request_factory")
def make_request_factory():
    return RequestFactory()


@pytest.fixture
def view_url(tp, election):
    return tp.reverse("election:vote", election_id=election.slug)

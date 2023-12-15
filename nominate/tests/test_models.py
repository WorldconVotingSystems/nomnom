from nominate.models import NominatingMemberProfile, Nomination, Category, Election
from django.contrib.auth import get_user_model
import pytest


@pytest.mark.django_db
@pytest.fixture(name="user")
def make_user():
    user = get_user_model()(username="test-u", password="test-p")
    user.save()
    return user


@pytest.mark.django_db
@pytest.fixture(name="nominator")
def make_nominator(user):
    nominator = NominatingMemberProfile(user=user)
    nominator.save()
    return nominator


@pytest.mark.django_db
@pytest.fixture(name="election")
def make_election():
    election = Election(slug="test-e", name="test-e name")
    election.save()
    return election


@pytest.mark.django_db
@pytest.fixture(name="category")
def make_category(election):
    category = Category(
        election=election,
        name="cat-e",
        description="cat-e-desc",
        ballot_position=1,
        fields=1,
        field_1_description="Field 1",
    )
    category.save()
    return category


@pytest.mark.django_db
def test_nomination_validation(category, nominator):
    Nomination(category=category, nominator=nominator).save()

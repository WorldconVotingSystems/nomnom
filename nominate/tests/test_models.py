from model_bakery import baker
import pytest

from nominate.models import Nomination

pytestmark = pytest.mark.usefixtures("db")


@pytest.fixture(name="nominator")
def make_nominator():
    return baker.make("nominate.NominatingMemberProfile")


@pytest.fixture(name="category")
def make_category():
    return baker.make(
        "nominate.Category",
        ballot_position=1,
        fields=1,
        field_1_description="Field 1",
    )


def test_nomination_validation(category, nominator):
    Nomination(category=category, nominator=nominator).save()

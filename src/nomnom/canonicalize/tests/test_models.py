import pytest

from nomnom.nominate.factories import (
    CategoryFactory,
    NominatingMemberProfileFactory,
    NominationFactory,
)


@pytest.fixture(name="set_of_nominations")
def make_set_of_nominations(election):
    """Create a standard set of nominations.

    This is all for a synthetic category.

    Create nominations for 5 different members, between 1 and 5 nominations
    per member.
    """

    category = CategoryFactory.create(election=election, fields=2, ballot_position=1)

    m1 = NominatingMemberProfileFactory.create()
    m2 = NominatingMemberProfileFactory.create()
    m3 = NominatingMemberProfileFactory.create()
    m4 = NominatingMemberProfileFactory.create()
    m5 = NominatingMemberProfileFactory.create()

    NominationFactory.create_batch(1, category=category, nominator=m1)
    NominationFactory.create_batch(2, category=category, nominator=m2)
    NominationFactory.create_batch(3, category=category, nominator=m3)
    NominationFactory.create_batch(4, category=category, nominator=m4)
    NominationFactory.create_batch(5, category=category, nominator=m5)


def test_fixture(set_of_nominations): ...

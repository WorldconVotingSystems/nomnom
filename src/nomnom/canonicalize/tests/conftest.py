import pytest

from nomnom.nominate.factories import CategoryFactory, ElectionFactory


@pytest.fixture(name="election")
def make_election(db):
    return ElectionFactory()


@pytest.fixture(name="category")
def make_category(election):
    """Create a category for the election."""
    return CategoryFactory.create(election=election, fields=2, ballot_position=1)

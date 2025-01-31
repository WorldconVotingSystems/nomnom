import pytest

from nomnom.nominate.factories import ElectionFactory


@pytest.fixture(name="election")
def make_election(db):
    return ElectionFactory()

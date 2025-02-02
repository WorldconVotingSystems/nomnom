import pytest
from django.db import IntegrityError

from nomnom.canonicalize.factories import WorkFactory
from nomnom.nominate.factories import (
    NominationFactory,
)


def test_nominations_can_only_associate_with_one_work(category):
    n1 = NominationFactory.create(category=category)
    w1 = WorkFactory.create(category=category)
    w2 = WorkFactory.create(category=category)

    w1.nominations.add(n1)
    with pytest.raises(IntegrityError):
        w2.nominations.add(n1)

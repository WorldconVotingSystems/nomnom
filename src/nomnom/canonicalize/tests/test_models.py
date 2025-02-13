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


def test_nomination_backreference_when_present(category):
    n1 = NominationFactory.create()
    w1 = WorkFactory.create()

    w1.nominations.add(n1)
    w1.save()
    n1.refresh_from_db()
    assert n1.work == w1


def test_nomination_backreference_when_absent(category):
    n1 = NominationFactory.create()
    assert n1.work is None

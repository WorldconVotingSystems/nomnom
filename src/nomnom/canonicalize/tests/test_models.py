import pytest
from django.db import IntegrityError

from nomnom.canonicalize.factories import WorkFactory
from nomnom.nominate import models as nominate
from nomnom.nominate.factories import (
    CategoryFactory,
    NominationFactory,
)

pytestmark = pytest.mark.usefixtures("db")


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


@pytest.mark.parametrize(
    "category",
    [
        CategoryFactory.build(fields=1),
        CategoryFactory.build(fields=2),
        CategoryFactory.build(fields=3),
    ],
)
def test_nomination_associates_with_work_with_matching_name(category):
    category.election.save()
    category.save()

    def nom(*names) -> nominate.Nomination:
        if category.fields == 1:
            return NominationFactory.create(category=category, field_1=names[0])
        elif category.fields == 2:
            return NominationFactory.create(
                category=category, field_1=names[0], field_2=names[1]
            )
        elif category.fields == 3:
            return NominationFactory.create(
                category=category, field_1=names[0], field_2=names[1], field_3=names[2]
            )

    existing_nom = nom("The Hobbit", "JRR", "Unwin")
    w1 = WorkFactory.create(category=category)
    w1.nominations.add(existing_nom)
    w1.save()

    new_nom = nom("The Hobbit", "JRR", "Unwin")
    new_nom.refresh_from_db()

    assert new_nom.work == w1

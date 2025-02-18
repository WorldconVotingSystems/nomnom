import pytest
from django.db import IntegrityError

from nomnom.canonicalize.factories import WorkFactory
from nomnom.canonicalize.models import CanonicalizedNomination, Work
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


def test_combine_works_moves_nominations(category):
    """Ensure nominations from other works are properly transferred."""
    w1 = WorkFactory.create(category=category)
    w2 = WorkFactory.create(category=category)

    n1 = NominationFactory.create(category=category)
    n2 = NominationFactory.create(category=category)

    w2.nominations.add(n1, n2)

    # Act: Merge w2 into w1
    w1.combine_works([w2])

    # Assert: All nominations now belong to w1
    assert set(w1.nominations.all()) == {n1, n2}


def test_combine_works_deletes_old_works(category):
    """Ensure the merged works are deleted after transfer."""
    w1 = WorkFactory.create(category=category)
    w2 = WorkFactory.create(category=category)

    n1 = NominationFactory.create(category=category)
    w2.nominations.add(n1)

    # Act: Merge and delete w2
    w1.combine_works([w2])

    # Assert: w2 no longer exists
    assert not Work.objects.filter(id=w2.id).exists()


def test_combine_works_handles_multiple_works(category):
    """Ensure multiple works can be merged correctly."""
    w1 = WorkFactory.create(category=category)
    w2 = WorkFactory.create(category=category)
    w3 = WorkFactory.create(category=category)

    n1 = NominationFactory.create(category=category)
    n2 = NominationFactory.create(category=category)
    n3 = NominationFactory.create(category=category)

    w2.nominations.add(n1, n2)
    w3.nominations.add(n3)

    # Act: Merge w2 and w3 into w1
    w1.combine_works([w2, w3])

    # Assert: All nominations are now in w1
    assert set(w1.nominations.all()) == {n1, n2, n3}
    assert not Work.objects.filter(id=w2.id).exists()
    assert not Work.objects.filter(id=w3.id).exists()


def test_combine_works_keeps_canonicalized_nominations_unique(category):
    """Ensure CanonicalizedNomination table maintains expected relationships after merging."""
    w1 = WorkFactory.create(category=category)
    w2 = WorkFactory.create(category=category)

    n1 = NominationFactory.create(category=category)
    n2 = NominationFactory.create(category=category)

    w1.nominations.add(n1)
    w2.nominations.add(n2)

    # Act: Merge w2 into w1
    w1.combine_works([w2])

    # Assert: Each nomination remains uniquely assigned in CanonicalizedNomination
    assert CanonicalizedNomination.objects.count() == 2
    assert set(
        CanonicalizedNomination.objects.values_list("nomination_id", flat=True)
    ) == {n1.id, n2.id}

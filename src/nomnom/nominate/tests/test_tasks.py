import pytest
from django.db.models import Max

from nomnom.canonicalize.factories import WorkFactory
from nomnom.nominate.factories import (
    CategoryFactory,
    NominatingMemberProfileFactory,
    NominationFactory,
)
from nomnom.nominate.models import Nomination
from nomnom.nominate.tasks import (
    link_nominations_to_works,
)

tasks = pytest.mark.parametrize("linking_task", [link_nominations_to_works])


@pytest.fixture(name="nominator")
def make_nominator():
    return NominatingMemberProfileFactory()


def next_id():
    max_id = Nomination.objects.aggregate(max_id=Max("id"))["max_id"]
    return max_id + 1 if max_id else 1


@tasks
def test_nominations_link_to_correct_work_within_same_category(
    db, nominator, linking_task
):
    """Nominations that match an existing Work in the same category should be linked."""
    category_a = CategoryFactory.create()
    work = WorkFactory.create(name="Work 1", category=category_a)

    nomination = NominationFactory.build(
        id=next_id(), category=category_a, field_1="Work 1", nominator=nominator
    )
    Nomination.objects.bulk_create([nomination])

    # Act: Run the task
    linking_task([nomination.id])
    nomination.refresh_from_db()

    # Assert: Nomination should be linked correctly
    assert nomination.work == work


@tasks
def test_nominations_link_to_work_by_nomination_name_alone(db, nominator, linking_task):
    """Nominations that match another nomination linked to a work in the same category should be linked."""
    category_a = CategoryFactory.create()
    work = WorkFactory.create(category=category_a)

    original_nomination = NominationFactory.build(
        id=next_id(), category=category_a, field_1="Work 1", nominator=nominator
    )
    Nomination.objects.bulk_create([original_nomination])
    work.nominations.add(original_nomination)

    nomination2 = NominationFactory.build(
        id=next_id(), category=category_a, field_1="Work 1", nominator=nominator
    )
    Nomination.objects.bulk_create([nomination2])
    nomination2.refresh_from_db()
    assert nomination2.work is None

    # Act: Run the task
    linking_task([nomination2.id])
    nomination2.refresh_from_db()

    # Assert: Both nominations should be linked to the same work
    assert nomination2.work == work

    assert work.nominations.all().count() == 2


@tasks
def test_nominations_do_not_cross_match_between_categories(db, nominator, linking_task):
    """Nominations in different categories should not incorrectly match existing Works."""
    category_a = CategoryFactory.create(name="Category A")
    category_b = CategoryFactory.create(name="Category B")

    WorkFactory.create(name="Work 1", category=category_a)

    # This nomination is in a different category but has the same name as Work 1 in Category A
    nomination_in_b = NominationFactory.build(
        id=next_id(), category=category_b, field_1="Work 1", nominator=nominator
    )
    Nomination.objects.bulk_create([nomination_in_b])

    # Act: Run the task
    linking_task([nomination_in_b.id])
    nomination_in_b.refresh_from_db()

    # Assert: The nomination in Category B should NOT be linked to the Work in Category A
    assert nomination_in_b.work is None


@tasks
def test_nominations_match_correct_canonical_work_by_category(
    db, nominator, linking_task
):
    """Ensure nominations in different categories match works in their respective categories."""
    category_a = CategoryFactory.create()
    category_b = CategoryFactory.create()

    work_in_a = WorkFactory.create(name="Work 1", category=category_a)
    work_in_b = WorkFactory.create(
        name="Work 1", category=category_b
    )  # Same name, different category

    nid = next_id()
    nomination_in_a = NominationFactory.build(
        id=nid, category=category_a, field_1="Work 1", nominator=nominator
    )
    nomination_in_b = NominationFactory.build(
        id=nid + 1, category=category_b, field_1="Work 1", nominator=nominator
    )
    Nomination.objects.bulk_create([nomination_in_a, nomination_in_b])

    # Act: Run task on both nominations
    linking_task([nomination_in_a.id, nomination_in_b.id])
    nomination_in_a.refresh_from_db()
    nomination_in_b.refresh_from_db()

    # Assert: Both nominations match the correct work in their respective categories
    assert nomination_in_a.work == work_in_a
    assert nomination_in_b.work == work_in_b

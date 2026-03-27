from contextlib import contextmanager

import pytest
from django.db import IntegrityError, connection
from django.test.utils import CaptureQueriesContext

from nomnom.canonicalize.factories import WorkFactory
from nomnom.canonicalize.models import CanonicalizedNomination, Work, group_nominations
from nomnom.nominate import models as nominate
from nomnom.nominate.factories import (
    CategoryFactory,
    NominatingMemberProfileFactory,
    NominationFactory,
)

pytestmark = pytest.mark.usefixtures("db")


@contextmanager
def no_inserts():
    with CaptureQueriesContext(connection) as context:
        try:
            rv = yield
        finally:
            ...

    for query in context.captured_queries:
        sql = query["sql"]
        assert not (sql.startswith("INSERT INTO ") or sql.startswith("UPDATE ")), (
            "The DB was unexpectedly updated:\n" + sql
        )

    return rv


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


def test_nomination_does_not_auto_link_to_similar_but_non_identical_work(category):
    """A nomination that is similar but not identical to an existing work
    should not be automatically linked by the post_save signal."""
    work = WorkFactory.create(name="The Hobbit", category=category)
    nomination = NominationFactory.create(category=category, field_1="The Hobbits")
    nomination.refresh_from_db()

    assert nomination.work is None
    assert nomination not in work.nominations.all()


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


def test_group_works_with_multiple_previous_works_overwrites(category):
    w1 = WorkFactory.create(category=category)
    w2 = WorkFactory.create(category=category)
    nominations = NominationFactory.create_batch(3)

    w1.nominations.add(nominations[0])
    w1.save()
    w2.nominations.add(nominations[1])
    w2.save()

    nominations = nominate.Nomination.objects.all()

    work = group_nominations(nominations, w2)

    ic(work)
    ic(nominations)

    assert set(work.nominations.all()) == set(nominations)
    assert all(
        nomination.work == work for nomination in nominate.Nomination.objects.all()
    )


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


@pytest.mark.parametrize(
    "fieldset, expected",
    [
        (["The Hobbit"], "The Hobbit"),
    ],
)
def test_proposed_works_permutations(category, fieldset, expected):
    """Ensure proposed_work_name generates expected permutations based on category fields."""
    nominator = NominatingMemberProfileFactory.create()
    nomination = nominate.Nomination(category=category, nominator=nominator)

    if category.fields >= 1:
        nomination.field_1 = fieldset[0]
    if category.fields >= 2 and len(fieldset) > 1:
        nomination.field_2 = fieldset[1]
    if category.fields >= 3 and len(fieldset) > 2:
        nomination.field_3 = fieldset[2]

    nomination.save()

    # Act: Get proposed work name
    proposed_name = nomination.proposed_work_name()

    # Assert: Proposed name should match expected permutation
    assert proposed_name == expected


@pytest.mark.parametrize("fields", [1, 2, 3])
def test_finds_matching_work_by_nomination_fields(db, fields):
    """Ensure a work is matched correctly based on a nomination's combined fields."""
    category = CategoryFactory.create(fields=fields)
    work = WorkFactory.create(name="The Hobbit Tolkien", category=category)

    nomination = NominationFactory.create(category=category)
    if fields == 1:
        nomination.field_1 = "The Hobbit Tolkien"
    elif fields == 2:
        nomination.field_1, nomination.field_2 = "The", "Hobbit Tolkien"
    elif fields == 3:
        nomination.field_1, nomination.field_2, nomination.field_3 = (
            "The",
            "Hobbit",
            "Tolkien",
        )
    nomination.save()

    # Act: Find work
    matched_work = Work.find_match_based_on_identical_nomination(
        nomination.proposed_work_name(), category
    )

    # Assert: Work must be found based on nomination's combined fields
    assert matched_work == work


def test_finds_matching_work_by_work_name(db):
    """Ensure a work is matched correctly based on an exact Work.name match."""
    category = CategoryFactory.create()
    work = WorkFactory.create(name="The Hobbit", category=category)

    nomination = NominationFactory.create(category=category, field_1="The Hobbit")

    # Act: Find work
    matched_work = Work.find_match_based_on_identical_nomination(
        nomination.proposed_work_name(), category
    )

    # Assert: Work should match directly by name
    assert matched_work == work


def test_finds_matching_work_ignoring_case(db):
    """Ensure Work is matched case-insensitively by name."""
    category = CategoryFactory.create()

    # Create Work with a slightly different case
    work = WorkFactory.create(name="The Hobbit", category=category)

    # Nomination with different casing
    nomination = NominationFactory.create(category=category, field_1="the hobbit")

    # Act: Find matching work
    matched_work = Work.find_match_based_on_identical_nomination(
        nomination.proposed_work_name(), category
    )

    # Assert: Should match even if case differs
    assert matched_work == work


@pytest.mark.parametrize("fields", [1, 2, 3])
def test_finds_matching_work_by_nomination_ignoring_case(db, fields):
    """Ensure nominations match a Work case-insensitively using field concatenation."""
    category = CategoryFactory.create(fields=fields)
    work = WorkFactory.create(name="The Hobbit tolkien", category=category)

    nomination = NominationFactory.create(category=category)

    if fields == 1:
        nomination.field_1 = "the hobbit tolkien"
    elif fields == 2:
        nomination.field_1, nomination.field_2 = "the", "HOBBIT tolkien"
    elif fields == 3:
        nomination.field_1, nomination.field_2, nomination.field_3 = (
            "THE",
            "hobbit",
            "TOLKIEN",
        )

    nomination.save()

    # Act: Find work
    matched_work = Work.find_match_based_on_identical_nomination(
        nomination.proposed_work_name(), category
    )

    # Assert: Should match even if field case varies
    assert matched_work == work


def test_find_matches_returns_multiple_results(db):
    """Ensure find_fuzzy_matches returns multiple similar works."""
    category = CategoryFactory.create()
    work1 = WorkFactory.create(name="The Hobbit", category=category)
    work2 = WorkFactory.create(
        name="The Hobbit: An Unexpected Journey", category=category
    )
    WorkFactory.create(name="Completely Different Title", category=category)

    results = Work.find_fuzzy_matches("The Hobbit", category)

    assert work1 in results
    assert work2 in results


def test_find_matches_ordered_by_similarity(db):
    """Ensure results are ordered by similarity, best match first."""
    category = CategoryFactory.create()
    fuzzy = WorkFactory.create(name="The Hobbits Journey", category=category)
    exact = WorkFactory.create(name="The Hobbit", category=category)

    results = Work.find_fuzzy_matches("The Hobbit", category)

    assert results[0] == exact
    assert fuzzy in results


def test_find_matches_respects_limit(db):
    """Ensure find_fuzzy_matches respects the limit parameter."""
    category = CategoryFactory.create()
    for i in range(5):
        WorkFactory.create(name=f"The Hobbit Volume {i}", category=category)

    results = Work.find_fuzzy_matches("The Hobbit", category, limit=2)

    assert len(results) <= 2


def test_find_matches_excludes_low_similarity(db):
    """Ensure works with low similarity are not returned."""
    category = CategoryFactory.create()
    WorkFactory.create(name="Completely Unrelated Title", category=category)

    results = Work.find_fuzzy_matches("The Hobbit", category)

    assert len(results) == 0


def test_find_matches_by_linked_nomination_fields(db):
    """Ensure matching works via nomination fields linked to a work."""
    category = CategoryFactory.create(fields=2)
    work = WorkFactory.create(name="Different Name Entirely", category=category)
    nomination = NominationFactory.create(
        category=category, field_1="The Hobbit", field_2="Tolkien"
    )
    work.nominations.add(nomination)

    results = Work.find_fuzzy_matches("The Hobbit Tolkien", category)

    assert work in results

import pytest

from nomnom.nominate import factories, models
from nomnom.wsfs.rules.constitution_2023 import ballots_from_category

# mark all tests in the module with @pytest.mark.django_db
pytestmark = pytest.mark.django_db


# This is a shorthand for ballot data. It's designed for a category with 4 finalists,
# and one "No Award" option. The No award option is in the fifth column.
#
# Each number indicates the rank for that finalist. A member will be assigned to each row.
# Any time this table changes, the tests will need to be updated.
#
# A None value indicates that the finalist was not ranked.
#
# This is a fixture so that tests can manipulate the data without changing the source.
@pytest.fixture(name="ballot_data")
def get_ballot_data():
    return [
        [1, 2, 3, 4, 5],
        [4, 3, 2, 1, 5],
        [5, 4, 3, None, 1],
        [1, 2, 3, 4, 5],
        [5, 2, 3, 4, 1],
        [3, 2, 5, 4, 1],
    ]


@pytest.fixture(name="ranked_finalists")
def get_ranked_finalists(category, ballot_data) -> list[models.Finalist]:
    finalists = list(category.finalist_set.all())
    for ballot in ballot_data:
        member = factories.NominatingMemberProfileFactory.create()

        for rank, finalist in zip(ballot, finalists):
            if rank is not None:
                factories.RankFactory.create(
                    membership=member, finalist=finalist, position=rank
                )

    return finalists


def test_ballots_from_category(category, ranked_finalists, ballot_data):
    eb = ballots_from_category(category)
    assert len(eb.ballots) == len(ballot_data)

    # Our ballot data has at least one candidate ranked, so we are sure that the first place candidate is in the list.
    assert all(b.ranked_candidates[0] in ranked_finalists for b in eb.ballots)


def test_exact_ballot_first_places(category, ranked_finalists):
    eb = ballots_from_category(category)

    # These are specific to the ballot data in the get_ballot_data fixture
    assert eb.ballots[0].ranked_candidates[0] == ranked_finalists[0]
    assert eb.ballots[1].ranked_candidates[0] == ranked_finalists[3]
    assert eb.ballots[2].ranked_candidates[0] == ranked_finalists[4]
    assert eb.ballots[3].ranked_candidates[0] == ranked_finalists[0]
    assert eb.ballots[4].ranked_candidates[0] == ranked_finalists[4]
    assert eb.ballots[5].ranked_candidates[0] == ranked_finalists[4]


def test_excluded_candidate(category, ranked_finalists):
    eb = ballots_from_category(category, excluded_finalists=[ranked_finalists[0]])

    # no ballot should have the excluded finalist in it.
    for ballot in eb.ballots:
        assert ranked_finalists[0].as_candidate() not in ballot.ranked_candidates


@pytest.fixture(name="election")
def make_election():
    return factories.ElectionFactory.create(state="voting")


@pytest.fixture(name="category")
def make_category(election) -> models.Category:
    category = factories.CategoryFactory.create(election=election)
    factories.FinalistFactory.create(category=category, name="col 0", ballot_position=1)
    factories.FinalistFactory.create(category=category, name="col 1", ballot_position=2)
    factories.FinalistFactory.create(category=category, name="col 2", ballot_position=3)
    factories.FinalistFactory.create(category=category, name="col 3", ballot_position=4)
    factories.FinalistFactory.create(
        category=category, name="no award", ballot_position=5
    )
    return category

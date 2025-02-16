import random
import time

import pytest
from faker import Faker
from rich.pretty import pprint

from nomnom.wsfs.rules import constitution_2023 as eph


def log_round(ballots, counts, eliminations):
    pprint({"ballots": ballots, "counts": counts, "eliminations": eliminations})


@pytest.fixture(name="works")
def make_works(faker):
    return [faker.sentence(nb_words=2) for _ in range(10)]


@pytest.fixture(name="ballots")
def make_simple_ballota(works):
    ballots: list[set[str]] = [
        set(works[5:]),
        set(works[5:]),
        {works[2], works[1]},
        {works[2], works[3]},
        {works[2], works[0]},
        {works[2], works[0]},
        {works[0], works[1], works[3], works[6]},
        {works[0], works[2], works[3], works[7]},
        {works[1], works[3], works[4], works[8]},
        {works[1], works[3], works[6], works[9]},
    ]

    return ballots


def assert_ballot_count_invariants(ballots, counts):
    assert sum(val.nominations for val in counts.values()) == sum(
        len(ballot) for ballot in ballots
    ), (
        "The total number of nominations should be the sum of the number of works on each ballot."
    )
    assert sum(val.points for val in counts.values()) == 60 * len(ballots), (
        "The total number of points should be 60 times the number of ballots."
    )
    all_works = set()
    for ballot in ballots:
        all_works |= ballot

    assert len(counts) == len(all_works), (
        "All works should be represented in the counts."
    )


def test_count_nominations_on_single_ballot(faker: Faker):
    ballot = {faker.name() for _ in range(5)}
    counts = eph.count_nominations([ballot])

    # the point total should be evenly split
    assert all(val.points == 12 for val in counts.values())

    # each value had one nomination
    assert all(val.nominations == 1 for val in counts.values())

    # the count should be the number of works on the single ballot
    assert len(counts) == 5

    assert_ballot_count_invariants([ballot], counts)


def test_count_nominations_on_multiple_full_ballots(faker: Faker):
    ballot_1 = {faker.sentence(nb_words=5) for _ in range(5)}
    ballot_2 = {faker.sentence(nb_words=5) for _ in range(2)}

    ballots = [ballot_1, ballot_2]

    overlaps = set(random.sample(list(ballot_1), k=3))

    ballot_2 |= overlaps

    ic(ballot_1, ballot_2)

    counts = eph.count_nominations(ballots)

    ic(counts)

    assert_ballot_count_invariants(ballots, counts)


def test_count_nominations_on_multiple_partial_ballots(faker: Faker):
    ballot_1 = {faker.sentence(nb_words=5) for _ in range(3)}
    ballot_2 = {faker.sentence(nb_words=5) for _ in range(2)}

    ballots = [ballot_1, ballot_2]

    ic(ballot_1, ballot_2)

    counts = eph.count_nominations(ballots)

    ic(counts)

    assert_ballot_count_invariants(ballots, counts)


def test_rank_nominations_with_fewest_points_single_ballot(faker: Faker):
    """This is a degenerate case.

    The 'fewest' is all of them."""
    ballot = {faker.sentence(nb_words=5) for _ in range(5)}
    counts = eph.count_nominations([ballot])

    fewest = eph.nominations_with_fewest_points(counts)

    assert len(fewest) == 5, "All works should be the fewest."


def test_rank_nominations_with_fewest_points_single_outlier(faker: Faker):
    """This is a reasonable case

    The 'fewest' is the two outliers."""

    ballot_1 = {faker.sentence(nb_words=5) for _ in range(5)}
    ballot_2 = {w for w in random.sample(list(ballot_1), k=4)} | {
        faker.sentence(nb_words=5)
    }
    counts = eph.count_nominations([ballot_1, ballot_2])

    fewest = eph.nominations_with_fewest_points(counts)

    assert len(fewest) == 2, "The two outlier works should be fewest"


def test_rank_nominations_with_fewest_points_single_short_ballot(faker: Faker):
    """This is a degenerate case.

    The 'fewest' is all of them, because the second-most common will be the rest."""

    ballot_1 = {faker.sentence(nb_words=5) for _ in range(5)}
    ballot_2 = {w for w in random.sample(list(ballot_1), k=4)}
    ballots = [ballot_1, ballot_2]
    counts = eph.count_nominations(ballots)

    fewest = eph.nominations_with_fewest_points(counts)
    ic(ballots)
    ic(counts)
    assert len(fewest) == 5, "All works will appear"


def test_counts_on_simple_ballots(works, ballots):
    counts = eph.count_nominations(ballots)

    ic(counts)
    assert_ballot_count_invariants(ballots, counts)

    assert counts[works[0]].nominations == 4
    assert counts[works[1]].nominations == 4
    assert counts[works[2]].nominations == 5
    assert counts[works[3]].nominations == 5
    assert counts[works[4]].nominations == 1
    assert counts[works[5]].nominations == 2
    assert counts[works[6]].nominations == 4
    assert counts[works[7]].nominations == 3
    assert counts[works[8]].nominations == 3
    assert counts[works[9]].nominations == 3

    # we know some point values will vary
    assert counts[works[0]].points > counts[works[1]].points
    assert counts[works[2]].points > counts[works[3]].points


def test_eph_ballot_simple(works, ballots):
    """Test with 10 works.

    2 ballots are identical, consisting of works 5-10.
    4 ballots containe nomination 3

    4 ballots with 3 nominations from 1-5"""
    finalists = eph.eph(ballots, finalist_count=4, record_steps=log_round)

    ic(finalists)

    # from this set, we expect works[2] to be in the finalists:
    assert works[2] in finalists

    # works[6] despite being on the slate, also has 2 other nominations, so it should be in the
    # finalists
    assert works[6] in finalists

    # works[3] is found on 5 ballots.
    assert works[3] in finalists

    # works[0] is found on 4 ballots, 2 of them the 2-nomination ballots.
    # compared to works[1] which is also on 4 ballots, but only one of them is a 2-nomination ballot.
    assert works[0] in finalists


def test_eph_speed_on_realistic_data(faker):
    ballot_count = 1_500
    works_count = 500
    works = [faker.sentence(nb_words=2) for _ in range(works_count)]

    ballots = [
        set(random.sample(works, k=random.randint(1, 5))) for _ in range(ballot_count)
    ]

    start_time = time.monotonic()
    eph.eph(ballots, finalist_count=6)
    end_time = time.monotonic()

    ic(end_time - start_time)

    # with 1,500 ballots, this takes about 0.17 seconds on my machine.
    # that's pretty reasonable.

    # uncomment this to see the timing
    # assert False

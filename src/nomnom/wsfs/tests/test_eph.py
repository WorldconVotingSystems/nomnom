import random
import time
from collections import Counter
from collections.abc import Collection, Iterable

import pytest
from faker import Faker
from rich.pretty import pprint

from nomnom.wsfs.rules import constitution_2023 as eph


def as_ballots(ballots: Iterable[Collection[str]]) -> list[Counter[str]]:
    """The counting functions take one Counter per member; fixtures are easier to
    read as plain sets and lists."""
    return [Counter(ballot) for ballot in ballots]


def log_round(ballots, counts, eliminations):
    pprint({"ballots": ballots, "counts": counts, "eliminations": eliminations})


@pytest.fixture(name="works")
def make_works(faker):
    return [faker.sentence(nb_words=2) for _ in range(10)]


@pytest.fixture(name="ballots")
def make_simple_ballota(works):
    return as_ballots(
        [
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
    )


def assert_ballot_count_invariants(ballots, counts):
    assert sum(val.nominations for val in counts.values()) == sum(
        ballot.total() for ballot in ballots
    ), (
        "The total number of nominations should be the sum of the number of works written down on each ballot."
    )
    assert sum(val.ballot_count for val in counts.values()) == sum(
        len(ballot) for ballot in ballots
    ), "The total ballot count should be the sum of the distinct works on each ballot."
    assert sum(val.points for val in counts.values()) == 60 * len(ballots), (
        "The total number of points should be 60 times the number of ballots."
    )
    all_works = set()
    for ballot in ballots:
        all_works.update(ballot)

    assert len(counts) == len(all_works), (
        "All works should be represented in the counts."
    )


def test_count_nominations_on_single_ballot(faker: Faker):
    ballots = as_ballots([{faker.name() for _ in range(5)}])
    counts = eph.count_nominations(ballots)

    # the point total should be evenly split
    assert all(val.points == 12 for val in counts.values())

    # each value had one nomination
    assert all(val.nominations == 1 for val in counts.values())

    # the count should be the number of works on the single ballot
    assert len(counts) == 5

    assert_ballot_count_invariants(ballots, counts)


def test_count_nominations_on_multiple_full_ballots(faker: Faker):
    ballot_1 = {faker.sentence(nb_words=5) for _ in range(5)}
    ballot_2 = {faker.sentence(nb_words=5) for _ in range(2)}

    overlaps = set(random.sample(list(ballot_1), k=3))

    ballot_2 |= overlaps

    ic(ballot_1, ballot_2)

    ballots = as_ballots([ballot_1, ballot_2])
    counts = eph.count_nominations(ballots)

    ic(counts)

    assert_ballot_count_invariants(ballots, counts)


def test_count_nominations_on_multiple_partial_ballots(faker: Faker):
    ballot_1 = {faker.sentence(nb_words=5) for _ in range(3)}
    ballot_2 = {faker.sentence(nb_words=5) for _ in range(2)}

    ballots = as_ballots([ballot_1, ballot_2])

    ic(ballot_1, ballot_2)

    counts = eph.count_nominations(ballots)

    ic(counts)

    assert_ballot_count_invariants(ballots, counts)


def test_rank_nominations_with_fewest_points_single_ballot(faker: Faker):
    """This is a degenerate case.

    The 'fewest' is all of them."""
    ballot = {faker.sentence(nb_words=5) for _ in range(5)}
    counts = eph.count_nominations(as_ballots([ballot]))

    fewest = eph.nominations_with_fewest_points(counts)

    assert len(fewest) == 5, "All works should be the fewest."


def test_rank_nominations_with_fewest_points_single_outlier(faker: Faker):
    """This is a reasonable case

    The 'fewest' is the two outliers."""

    ballot_1 = {faker.sentence(nb_words=5) for _ in range(5)}
    ballot_2 = {w for w in random.sample(list(ballot_1), k=4)} | {
        faker.sentence(nb_words=5)
    }
    counts = eph.count_nominations(as_ballots([ballot_1, ballot_2]))

    fewest = eph.nominations_with_fewest_points(counts)

    assert len(fewest) == 2, "The two outlier works should be fewest"


def test_rank_nominations_with_fewest_points_single_short_ballot(faker: Faker):
    """This is a degenerate case.

    The 'fewest' is all of them, because the second-most common will be the rest."""

    ballot_1 = {faker.sentence(nb_words=5) for _ in range(5)}
    ballot_2 = {w for w in random.sample(list(ballot_1), k=4)}
    ballots = as_ballots([ballot_1, ballot_2])
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

    ballots = as_ballots(
        set(random.sample(works, k=random.randint(1, 5))) for _ in range(ballot_count)
    )

    start_time = time.monotonic()
    eph.eph(ballots, finalist_count=6)
    end_time = time.monotonic()

    ic(end_time - start_time)

    # with 1,500 ballots, this takes about 0.17 seconds on my machine.
    # that's pretty reasonable.

    # uncomment this to see the timing
    # assert False


def test_eph_first_round_counts_with_multiple_identical_nominations_on_one_ballot(
    faker,
):
    ballot_1 = {faker.sentence(nb_words=2).rstrip(".") for _ in range(5)}
    bullet = random.choice(list(ballot_1))
    ballot_2 = [bullet, bullet]
    ballots = as_ballots([ballot_1, ballot_2])

    steps = []

    def recorder(ballots: list[str], counts, eliminations):
        steps.append((ballots, counts, eliminations))

    finalists = eph.eph(ballots, finalist_count=1, record_steps=recorder)

    # the first step should only show two nominations for the bullet
    step = steps[0]
    counts = step[1]

    assert counts[bullet].nominations == 3
    assert counts[bullet].ballot_count == 2, f"Expected '{bullet}' to be on 2 ballots."

    assert finalists == [bullet], "The bullet should be the finalist."


def test_repeated_nomination_counts_as_one_ballot_however_the_ballots_arrive():
    """A member entering the same work twice has still only nominated it once.

    Canonicalization can merge variant spellings, so a ballot can legitimately name
    the same work twice; that is one nominating ballot whichever ballot it's on."""
    repeated = ["The Skiffy and Fanty Show", "The Skiffy and Fanty Show"]
    alongside = {"The Skiffy and Fanty Show", "Octothorpe"}

    for description, raw_ballots in [
        ("repeated ballot last", [alongside, repeated]),
        ("repeated ballot first", [repeated, alongside]),
    ]:
        ballots = as_ballots(raw_ballots)
        counts = eph.count_nominations(ballots)
        assert_ballot_count_invariants(ballots, counts)

        assert counts["The Skiffy and Fanty Show"].ballot_count == 2, (
            f"{description}: the work is on 2 ballots"
        )
        assert counts["The Skiffy and Fanty Show"].nominations == 3, (
            f"{description}: the work was written down 3 times"
        )


def test_repeated_nomination_does_not_dilute_the_rest_of_its_ballot():
    """A ballot always spreads its 60 points over the works it nominates.

    Writing one of them down twice earns no second share."""
    ballots = as_ballots([["Octothorpe", "Octothorpe", "Hugos There"]])
    counts = eph.count_nominations(ballots)
    assert_ballot_count_invariants(ballots, counts)

    assert counts["Octothorpe"].points == 30
    assert counts["Hugos There"].points == 30


def test_repeated_nomination_does_not_underpay_a_full_ballot():
    """A member who wrote one work down twice has nominated four works, not five.

    So the other three are due a quarter each, not a fifth."""
    ballots = as_ballots(
        [
            [
                "A Meal of Thorns",
                "A Meal of Thorns",
                "Octothorpe",
                "Hugos There",
                "Hugo, Girl!",
            ]
        ]
    )

    counts = eph.count_nominations(ballots)

    assert counts["A Meal of Thorns"].points == 15, (
        "the duplicated work takes one share of the ballot, not two"
    )
    for co_nominee in ["Octothorpe", "Hugos There", "Hugo, Girl!"]:
        assert counts[co_nominee].points == 15, (
            f"{co_nominee} shares the ballot with 3 other works, so it is due a quarter"
        )

    assert_ballot_count_invariants(ballots, counts)


def test_repeated_nomination_is_reported_the_same_way_in_every_round():
    """A surviving work's nomination counts hold steady from round to round.

    Eliminating other works shrinks the ballots a work shares, but never changes how
    many ballots named it or how many times it was written down."""
    ballots = as_ballots(
        [
            ["A Meal of Thorns", "A Meal of Thorns", "Hugo, Girl!"],
            ["A Meal of Thorns", "Octothorpe"],
            ["Hugo, Girl!"],
            ["Hugo, Girl!"],
        ]
    )

    steps = []
    eph.eph(ballots, finalist_count=2, record_steps=lambda b, c, e: steps.append(c))

    counted = [
        (step["A Meal of Thorns"].nominations, step["A Meal of Thorns"].ballot_count)
        for step in steps
        if "A Meal of Thorns" in step
    ]

    assert len(counted) > 1, "the work should survive at least one elimination"
    assert set(counted) == {(3, 2)}, (
        f"expected (3 nominations, 2 ballots) in every round, got {counted}"
    )


def test_elimination_compares_ballots_not_times_written_down():
    """The elimination phase eliminates the work fewest ballots nominated.

    > the nominee with the fewest number of nominations shall be eliminated

    A nomination is a ballot naming the work, so a work two members each wrote down
    twice loses to a work three members each named once — even though more entries
    mention it."""
    # Repeated is named by 3 ballots but written down 5 times; Single is named by
    # 4 ballots and written down 4 times. The bullet ballots keep the two filler
    # works clear of the bottom two on points.
    ballots = as_ballots(
        [
            ["Repeated", "Repeated", "Filler One"],
            ["Repeated", "Repeated", "Filler One"],
            ["Repeated", "Filler Two"],
            ["Single", "Filler One"],
            ["Single", "Filler One"],
            ["Single", "Filler Two"],
            ["Single", "Filler Two"],
            ["Filler One"],
            ["Filler Two"],
        ]
    )

    steps = []
    finalists = eph.eph(
        ballots, finalist_count=3, record_steps=lambda b, c, e: steps.append((c, e))
    )

    counts, eliminations = steps[0]
    assert (counts["Repeated"].nominations, counts["Repeated"].ballot_count) == (5, 3)
    assert (counts["Single"].nominations, counts["Single"].ballot_count) == (4, 4)

    assert eliminations == ["Repeated"], (
        "the work on the fewest ballots should be eliminated"
    )
    assert "Single" in finalists

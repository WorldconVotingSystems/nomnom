import random
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from nomnom.nominate import models as nominate

from rich.pretty import pprint

from nomnom.canonicalize import models as canonicalize
from nomnom.canonicalize.factories import WorkFactory
from nomnom.nominate.factories import NominatingMemberProfileFactory
from nomnom.wsfs.rules import eph


@pytest.fixture(name="works", autouse=True)
def make_works(category):
    # I think 500 works are a good number to test with.
    WorkFactory.create_batch(500, category=category)


def ballot_factory(
    category: "nominate.Category",
    nominator: "nominate.NominatingMemberProfile",
    number_of_works=None,
):
    """A canonicalized ballot consists of between 1 and 5 works, all in the same category."""

    works_in_category = canonicalize.Work.objects.filter(category=category)

    weighted_choices = [5] * 60 + [4] * 20 + [3] * 10 + [2] * 7 + [1] * 3
    if number_of_works is None:
        number_of_works = random.choice(weighted_choices)

    works = random.sample(list(works_in_category), number_of_works)
    works = works + [None] * (5 - number_of_works)

    return canonicalize.CategoryBallot(
        category=category,
        nominator=nominator,
        work_1=works[0],
        work_2=works[1],
        work_3=works[2],
        work_4=works[3],
        work_5=works[4],
    )


def _test_eph_on_single_ballot(works, category):
    # we expect that one ballot cannot give us a full set of nominated works. Nevertheless, we
    # know what this will look like.

    ballot = ballot_factory(
        category, NominatingMemberProfileFactory.create(), number_of_works=5
    )

    pprint(ballot)

    finalists = eph([ballot], finalist_count=5, record_steps=None)
    assert len(finalists) == 5

    work_names = [w.name for w in ballot.works]

    assert all(name in finalists for name in work_names)

    assert False

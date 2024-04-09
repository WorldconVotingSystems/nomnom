from dataclasses import dataclass
from itertools import groupby
from operator import attrgetter
from collections.abc import Iterable

import nominate.models
from pyrankvote import Ballot, Candidate


@dataclass
class ElectionBallots:
    candidates: Iterable[Candidate]
    ballots: Iterable[Ballot]


def ballots_from_category(category: nominate.models.Category) -> ElectionBallots:
    candidates_by_finalist = {
        finalist: Candidate(finalist.name) for finalist in category.finalist_set.all()
    }
    ballots = []
    # group our ranks by nominating member, and then make a ballot for each one.
    for member, ranks in groupby(
        sorted(category.rank_set.all(), key=attrgetter("membership")),
        key=attrgetter("membership"),
    ):
        ranks = sorted(ranks, attrgetter("position"))
        ballot = Ballot([candidates_by_finalist[rank.finalist] for rank in ranks])
        ballots.append(ballot)

    return ElectionBallots(candidates=candidates_by_finalist.values(), ballots=ballots)

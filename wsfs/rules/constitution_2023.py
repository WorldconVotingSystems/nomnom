from collections.abc import Iterable
from dataclasses import dataclass
from itertools import groupby
from operator import attrgetter

from nominate import models
from pyrankvote import Ballot, Candidate


@dataclass
class ElectionBallots:
    candidates: Iterable[Candidate]
    ballots: Iterable[Ballot]


def ballots_from_category(category: models.Category) -> ElectionBallots:
    candidates_by_finalist = {
        finalist: Candidate(finalist.name) for finalist in category.finalist_set.all()
    }
    ballots = []
    # group our ranks by nominating member, and then make a ballot for each one.
    category_ranks = models.Rank.objects.select_related(
        "membership", "finalist", "finalist__category"
    ).filter(finalist__category=category)
    for member, ranks in groupby(
        sorted(category_ranks, key=lambda r: r.membership.id),
        key=attrgetter("membership"),
    ):
        ranks = sorted(ranks, key=attrgetter("position"))
        ballot = Ballot([candidates_by_finalist[rank.finalist] for rank in ranks])
        ballots.append(ballot)

    return ElectionBallots(candidates=candidates_by_finalist.values(), ballots=ballots)

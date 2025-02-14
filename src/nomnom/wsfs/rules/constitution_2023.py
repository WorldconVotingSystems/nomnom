import math
from dataclasses import dataclass
from itertools import groupby
from operator import attrgetter
from typing import Protocol

from pyrankvote import Ballot, Candidate
from pyrankvote.helpers import (
    CompareMethodIfEqual,
    ElectionManager,
    ElectionResults,
)

from nomnom.convention import HugoAwards
from nomnom.nominate import models


@dataclass
class ElectionBallots:
    candidates: list[Candidate]
    ballots: list[Ballot]


def ballots_from_category(
    category: models.Category, excluded_finalists: list[models.Finalist] | None = None
) -> ElectionBallots:
    exclude = excluded_finalists if excluded_finalists is not None else []
    exclude_pks = [e.pk for e in exclude]

    finalist_query = category.finalist_set.exclude(pk__in=exclude_pks)
    candidates_by_finalist = {
        finalist: finalist.as_candidate() for finalist in finalist_query
    }

    finalist_ids = [finalist.id for finalist in finalist_query]

    ballots = []

    # group our ranks by nominating member, and then make a ballot for each one.
    category_ranks = models.Rank.valid.select_related("finalist").filter(
        finalist_id__in=finalist_ids
    )
    for member_id, ranks in groupby(
        sorted(category_ranks, key=lambda r: r.membership_id),
        key=attrgetter("membership_id"),
    ):
        ranks = sorted(ranks, key=attrgetter("position"))
        ballot = Ballot([candidates_by_finalist[rank.finalist] for rank in ranks])
        ballots.append(ballot)

    return ElectionBallots(
        candidates=list(candidates_by_finalist.values()), ballots=ballots
    )


def hugo_voting(
    candidates: list[Candidate],
    ballots: list[Ballot],
    runoff_candidate: Candidate | None = None,
) -> ElectionResults:
    # Because we're working with floating point, we need to account for rounding errors.
    # TODO: see how performance is affected if we switch to Decimal
    rounding_error = 1e-6
    if runoff_candidate is None:
        maybe_no_award = [c for c in candidates if c.name.lower() == "no award"]
        if maybe_no_award:
            runoff_candidate = maybe_no_award[0]

    manager = ElectionManager(
        candidates,
        ballots,
        number_of_votes_pr_voter=1,
        compare_method_if_equal=CompareMethodIfEqual.MostSecondChoiceVotes,
        pick_random_if_blank=False,
    )
    results = ElectionResults()

    winners_allowed = 1

    # Remove the worst candidate and transfer votes until we have a winner or a tie
    while True:
        majority_threshold = math.ceil(
            manager.get_number_of_non_exhausted_ballots() / 2
        )

        finalists = manager.get_candidates_in_race()
        if not finalists:
            raise RuntimeError("No finalists")

        finalist_votes = {c: manager.get_number_of_votes(c) for c in finalists}

        votes_remaining = sum(finalist_votes.values())
        finalists_to_elect = []

        # we keep this outside of the manager because we use it to determine
        # which candidates' votes are being redistributed.
        finalists_to_reject = []

        for i, finalist in enumerate(finalists):
            votes_for_finalist = finalist_votes[finalist]

            if majority_threshold - votes_for_finalist <= rounding_error:
                finalists_to_elect.append(finalist)

            # IRV PROCESS BELOW: reject more than one, if redistributing their votes can't
            # change the results.
            #
            # Reject candidates that even with redistribution can't change the results
            # elif (
            #     i >= remaining_winners
            #     and votes_remaining - rounding_error <= last_votes
            # ):
            #     finalists_to_reject.append(finalist)
            #
            # elif is_last_finalist:
            #     raise RuntimeError("Illegal state: No candidate can be rejected")

            votes_remaining -= votes_for_finalist

        # reject the finalist with the fewest votes.
        # if there are multiple candidates with the same number of votes, reject them all.
        if manager.get_candidate_with_least_votes_in_race() not in finalists_to_elect:
            finalists_to_reject.append(manager.get_candidate_with_least_votes_in_race())

        # fewest_votes = min(finalist_votes.values())
        # for finalist, votes in finalist_votes.items():
        #     if votes == fewest_votes:
        #         finalists_to_reject.append(finalist)
        for finalist in finalists_to_elect:
            manager.elect_candidate(finalist)

        # reject finalists in reverse order (not sure why)
        for finalist in finalists_to_reject[::-1]:
            manager.reject_candidate(finalist)

        # If we leave that loop with only one finalist remaining, they win
        seats_left = winners_allowed - manager.get_number_of_elected_candidates()
        if manager.get_number_of_candidates_in_race() <= seats_left:
            for finalist in manager.get_candidates_in_race():
                finalists_to_elect.append(finalist)
                manager.elect_candidate(finalist)

        # if we've run out of winner slots (1), nobody else can win
        if seats_left == 0:
            for finalist in manager.get_candidates_in_race()[::-1]:
                finalists_to_reject.append(finalist)
                manager.reject_candidate(finalist)

        results.register_round_results(manager.get_results())

        if manager.get_number_of_candidates_in_race() == 0:
            break

        # transfer votes from rejected finalists to the remaining ones.
        for finalist in finalists_to_reject:
            number_of_votes = manager.get_number_of_votes(finalist)
            manager.transfer_votes(finalist, number_of_votes)

        # new round!
        continue  # explicit, but unnecessary

    # by here we must have _a_ winner at least. Maybe more.
    if len(results.get_winners()) == 0:
        raise RuntimeError("No winners were elected")

    # We have a runoff against No Award; any ballot that ranked the runoff canidate over the winner here
    # is tallied. If that wins, then no award is granted in the category.
    if runoff_candidate is not None:
        winners = results.get_winners()
        runoff_candidates = winners[:]
        runoff_candidates.append(runoff_candidate)

        truncated_ballots = [
            Ballot([b for b in ballot.ranked_candidates if b in runoff_candidates])
            for ballot in ballots
        ]

        runoff_manager = ElectionManager(runoff_candidates, truncated_ballots)
        # by definition, all of our winners must have the same number of votes, so this is a simple
        # check:
        if runoff_manager.get_number_of_votes(
            runoff_candidate
        ) > runoff_manager.get_number_of_votes(winners[0]):
            runoff_manager.elect_candidate(runoff_candidate)
            for w in winners:
                if w in runoff_manager.get_candidates_in_race():
                    runoff_manager.reject_candidate(w)
        else:
            for w in winners:
                runoff_manager.elect_candidate(w)
            if runoff_candidate in runoff_manager.get_candidates_in_race():
                runoff_manager.reject_candidate(runoff_candidate)

        results.register_round_results(runoff_manager.get_results())

    return results


hugo_awards = HugoAwards(
    results_class=ElectionResults, counter=hugo_voting, hugo_nominations_per_member=5
)


@dataclass
class CountData:
    nominations: int = 0
    points: int = 0


class StepRecorder(Protocol):
    def __call__(
        self,
        ballots: list[set[str]],
        counts: dict[str, CountData],
        eliminations: list[str],
    ) -> None: ...


def null_recorder(
    ballots: list[set[str]],
    counts: dict[str, CountData],
    eliminations: list[str],
) -> None:
    pass


def eliminate_works(ballots: list[set[str]], eliminations: list[str]) -> list[set[str]]:
    eliminations_set = set(eliminations)
    cleaned_ballots = [set(ballot) - eliminations_set for ballot in ballots]
    return [ballot for ballot in cleaned_ballots if len(ballot) > 0]


def eph(
    # ballots are a flat list of work names; we assume canonicalization has occurred
    # the ballots _will_ be mutated.
    ballots: list[set[str]],
    finalist_count: int = 6,
    record_steps: StepRecorder = null_recorder,
):
    """Implement the EPH ballot construction algorithm."""

    while len(ballots) > 0:
        counts = count_nominations(ballots)
        eliminations = nominations_for_elimination(counts)
        next_size = len(counts) - len(eliminations)
        record_steps(
            ballots, counts, [] if next_size < finalist_count else eliminations
        )
        if next_size == finalist_count:
            return [work for work in counts.keys() if work not in eliminations]

        if next_size < finalist_count:
            return list(counts.keys())

        ballots = eliminate_works(ballots, eliminations)


def count_nominations(ballots: list[set[str]]) -> dict[str, CountData]:
    points_per_ballot = (
        60  # chosen because it means we don't need to deal with floating-point math.
    )
    counts: dict[str, CountData] = {}
    for ballot in ballots:
        divisor = len(ballot)
        nomination_points = points_per_ballot // divisor

        for work in ballot:
            count = counts.get(work)
            if count is None:
                count = CountData(nominations=1, points=nomination_points)
                counts[work] = count
            else:
                count.nominations += 1
                count.points += nomination_points

    return counts


def nominations_with_fewest_points(
    counts: dict[str, CountData],
) -> dict[str, CountData]:
    """Select two nominations with the fewest points.

    In case of tied for fewest, return all tied nominations.

    In case of one nomination with fewest, and tied for second-fewest, return all tied nominations as well.

    If there are only two nominations, return both."""
    if len(counts) <= 2:
        return counts

    # make a dict of points to lists of works
    by_points = {}
    for work, data in counts.items():
        by_points.setdefault(data.points, []).append(work)

    fewest_points = min(by_points.keys())

    fewest = {work: counts[work] for work in by_points[fewest_points]}
    if len(fewest) >= 2:
        # we have enough here; no need to go looking for second place
        return fewest

    # we need to get the second fewest as well.
    del by_points[fewest_points]

    fewest_points = min(by_points.keys())
    fewest.update({work: counts[work] for work in by_points[fewest_points]})

    assert len(fewest) >= 2

    return fewest


def nominations_with_fewest_nominations(
    counts: dict[str, CountData],
) -> dict[str, CountData]:
    """Select two nominations with the fewest nominations.

    Select the entry or entries of `counts` with the least nominations and of
    those, the entry or entries with the lowest point counts.

    This performs part of the Finalist Selection Process Elimination Phase:
    > Nominees chosen in the Selection Phase shall be compared, and the nominee
    > with the fewest number of nominations shall be eliminated and removed from
    > all ballots for the Calculation Phase of all subsequent rounds. [If] two or
    > more nominees are tied for the fewest number of nominations, the nominee
    > with the lowest point total at that round shall be eliminated. [If] two or
    > more nominees are tied for both fewest number of nominations and lowest
    > point total, then all such nominees tied at that round shall be eliminated.
    """
    fewest_nominations = min(counts.values(), key=attrgetter("nominations")).nominations
    fewest = {
        work: count
        for work, count in counts.items()
        if count.nominations == fewest_nominations
    }

    if len(fewest) > 1:
        fewest_points = min(fewest.values(), key=attrgetter("points")).points
        fewest = {
            work: count
            for work, count in fewest.items()
            if count.points == fewest_points
        }

    return fewest


def nominations_for_elimination(counts: dict[str, CountData]) -> list[str]:
    """Return the list of works to be eliminated."""
    fewest_points = nominations_with_fewest_points(counts)
    fewest_nominations = nominations_with_fewest_nominations(fewest_points)
    return list(fewest_nominations.keys())

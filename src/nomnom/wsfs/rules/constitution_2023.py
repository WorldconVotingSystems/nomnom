import math
from collections import Counter
from dataclasses import dataclass
from itertools import groupby
from operator import attrgetter
from typing import Protocol

import structlog
from pyrankvote import Ballot, Candidate
from pyrankvote.helpers import (
    CompareMethodIfEqual,
    ElectionManager,
    ElectionResults,
)

from nomnom.convention import HugoAwards
from nomnom.nominate import models

logger = structlog.get_logger("constitution_2023")


@dataclass
class ElectionBallots:
    candidates: list[Candidate]
    ballots: list[Ballot]


type NominatingBallotType = Counter[str]
type NominatingBallots = list[NominatingBallotType]


class NoFinalists(Exception): ...


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


# Because we're working with floating point, we need to account for rounding errors.
# TODO: see how performance is affected if we switch to Decimal
_ROUNDING_ERROR = 1e-6

# Hugo Award voting elects a single winner per category.
_WINNERS_ALLOWED = 1


def _find_no_award(candidates: list[Candidate]) -> Candidate | None:
    """Locate the 'No Award' candidate among the given candidates, if any."""
    for c in candidates:
        if c.name.lower() == "no award":
            return c
    return None


def _count_first_place_votes(
    candidates: list[Candidate], ballots: list[Ballot]
) -> Counter:
    """Count first-place votes for each candidate.

    Used as a tiebreaker when multiple candidates are tied for elimination.
    """
    first_places = Counter({c: 0 for c in candidates})
    for ballot in ballots:
        first_places[ballot.ranked_candidates[0]] += 1
    return first_places


def _finalists_meeting_majority(
    finalists: list[Candidate],
    finalist_votes: dict[Candidate, float],
    majority_threshold: float,
    log,
) -> list[Candidate]:
    """Return finalists whose votes meet or exceed the majority threshold."""
    to_elect = []
    for finalist in finalists:
        votes = finalist_votes[finalist]
        if majority_threshold - votes <= _ROUNDING_ERROR:
            log.debug("Propose to elect", finalist=finalist.name, votes=votes)
            to_elect.append(finalist)
    return to_elect


def _finalists_to_eliminate(
    manager: ElectionManager,
    first_places: Counter,
    finalists_to_elect: list[Candidate],
    log,
) -> list[Candidate]:
    """Determine which finalists to reject this round.

    Rules:
    * Reject the finalist with the fewest votes.
    * If there are multiple candidates tied for fewest votes, reject the one
      with the fewest original first-place votes.
    * If there are multiple candidates tied on both, reject them all.

    pyrankvote doesn't handle ties for last place natively, so we reach into
    its internals to inspect per-candidate vote counts.
    """
    assert len(manager._candidates_in_race) > 0, (
        "Can't get here without some candidates left"
    )

    # Step 1: candidates tied for fewest votes
    least_voted_vc = all_min(
        manager._candidates_in_race, key=lambda vc: vc.number_of_votes
    )
    last_place_vote_count = least_voted_vc[0].number_of_votes
    candidates_with_least_votes = [vc.candidate for vc in least_voted_vc]
    log.debug(
        "Checking tiebreak counts",
        last_place_vote_count=last_place_vote_count,
        candidates_with_least_votes=len(candidates_with_least_votes),
    )

    # Step 2: among those, candidates tied for fewest first-place votes
    first_place_tiebreak = all_min(
        candidates_with_least_votes, key=lambda c: first_places[c]
    )
    log.debug("First place tiebreak", candidates=[c.name for c in first_place_tiebreak])

    to_reject = []
    for candidate in first_place_tiebreak:
        if candidate not in finalists_to_elect:
            log.debug(
                "Propose to reject as last place",
                candidate=candidate.name,
                votes=last_place_vote_count,
            )
            to_reject.append(candidate)
    return to_reject


def _apply_decisions(
    manager: ElectionManager,
    to_elect: list[Candidate],
    to_reject: list[Candidate],
    log,
) -> None:
    """Tell the manager to elect and reject the chosen finalists.

    Rejections are applied in reverse order (matching prior behavior).
    """
    for finalist in to_elect:
        manager.elect_candidate(finalist)
        log.debug(
            "Electing",
            finalist=finalist.name,
            elected=manager.get_number_of_elected_candidates(),
        )

    for finalist in reversed(to_reject):
        log.debug("Rejecting", finalist=finalist.name)
        manager.reject_candidate(finalist)


def _fill_or_drain_remaining_seats(
    manager: ElectionManager,
    finalists_to_elect: list[Candidate],
    finalists_to_reject: list[Candidate],
    log,
) -> None:
    """Handle the edge cases at the end of a round.

    * If the remaining candidates fit in the remaining seats, elect them all.
    * If we've already filled every seat, reject any stragglers.

    Mutates the elect/reject lists in place so the caller can use them for
    vote redistribution.
    """
    seats_left = _WINNERS_ALLOWED - manager.get_number_of_elected_candidates()

    if manager.get_number_of_candidates_in_race() <= seats_left:
        for finalist in manager.get_candidates_in_race():
            log.debug("Electing to fill remaining seats", finalist=finalist.name)
            finalists_to_elect.append(finalist)
            manager.elect_candidate(finalist)

    if seats_left <= 0:
        for finalist in reversed(manager.get_candidates_in_race()):
            log.debug(
                "No more seats left; rejecting remaining finalist",
                finalist=finalist.name,
            )
            finalists_to_reject.append(finalist)
            manager.reject_candidate(finalist)


def _transfer_rejected_votes(
    manager: ElectionManager, rejected: list[Candidate], log
) -> None:
    """Redistribute votes from this round's rejected candidates."""
    for finalist in rejected:
        number_of_votes = manager.get_number_of_votes(finalist)
        manager.transfer_votes(finalist, number_of_votes)
        log.debug(
            "Transferred votes",
            from_finalist=finalist.name,
            number_of_votes=number_of_votes,
        )


def _run_no_award_runoff(
    results: ElectionResults,
    ballots: list[Ballot],
    runoff_candidate: Candidate,
) -> None:
    """Run the final runoff of all winners against the No Award candidate.

    Any ballot ranking No Award above a winner is tallied. If No Award beats
    the winners, no award is granted in this category.
    """
    winners = results.get_winners()
    runoff_candidates = winners[:] + [runoff_candidate]

    truncated_ballots = [
        Ballot([c for c in ballot.ranked_candidates if c in runoff_candidates])
        for ballot in ballots
    ]

    runoff_manager = ElectionManager(runoff_candidates, truncated_ballots)

    # All winners have the same number of votes by construction, so we compare
    # No Award against any one of them.
    no_award_wins = runoff_manager.get_number_of_votes(
        runoff_candidate
    ) > runoff_manager.get_number_of_votes(winners[0])

    if no_award_wins:
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


def hugo_voting(
    candidates: list[Candidate],
    ballots: list[Ballot],
    runoff_candidate: Candidate | None = None,
) -> ElectionResults:
    if runoff_candidate is None:
        runoff_candidate = _find_no_award(candidates)

    # For tiebreaking during elimination
    first_places = _count_first_place_votes(candidates, ballots)
    logger.debug(
        "First place tallies",
        first_places={c.name: v for c, v in first_places.items()},
    )

    manager = ElectionManager(
        candidates,
        ballots,
        number_of_votes_pr_voter=1,
        compare_method_if_equal=CompareMethodIfEqual.MostSecondChoiceVotes,
        pick_random_if_blank=False,
    )
    results = ElectionResults()

    # Each iteration: find finalists meeting the majority threshold, identify
    # the worst finalist(s) for elimination, then redistribute their votes.
    while True:
        log = logger.bind(round=len(results.rounds) + 1)

        finalists = manager.get_candidates_in_race()
        if not finalists:
            raise NoFinalists("Cannot run an election with no finalists")

        majority_threshold = math.ceil(
            manager.get_number_of_non_exhausted_ballots() / 2
        )
        log = log.bind(finalists=len(finalists))
        log.debug(
            "Starting round",
            runoff_candidate=runoff_candidate.name if runoff_candidate else None,
            majority_threshold=majority_threshold,
        )

        finalist_votes = {c: manager.get_number_of_votes(c) for c in finalists}
        log.debug(
            "Votes for finalists",
            finalist_votes={c.name: v for c, v in finalist_votes.items()},
        )

        # Decide who to elect and who to reject this round. We track these
        # separately from the manager because we need to know which rejected
        # candidates' votes to redistribute below.
        finalists_to_elect = _finalists_meeting_majority(
            finalists, finalist_votes, majority_threshold, log
        )
        finalists_to_reject = _finalists_to_eliminate(
            manager, first_places, finalists_to_elect, log
        )

        # Edge case: if every remaining finalist would be eliminated and none
        # met the majority threshold, elect them all instead. The rules require
        # them to face No Award in a runoff rather than yield an empty result.
        if not finalists_to_elect and len(finalists_to_reject) == len(finalists):
            log.debug("Tie would reject all finalists. Punting to runoff")
            finalists_to_reject = []
            finalists_to_elect = list(finalists)

        _apply_decisions(manager, finalists_to_elect, finalists_to_reject, log)
        _fill_or_drain_remaining_seats(
            manager, finalists_to_elect, finalists_to_reject, log
        )

        results.register_round_results(manager.get_results())

        if manager.get_number_of_candidates_in_race() == 0:
            log.debug(
                "Round complete",
                elected=len(finalists_to_elect),
                rejected=len(finalists_to_reject),
            )
            break

        _transfer_rejected_votes(manager, finalists_to_reject, log)

    if len(results.get_winners()) == 0:
        raise RuntimeError("No winners were elected")

    if runoff_candidate is not None:
        _run_no_award_runoff(results, ballots, runoff_candidate)

    return results


hugo_awards = HugoAwards(
    results_class=ElectionResults, counter=hugo_voting, hugo_nominations_per_member=5
)


@dataclass
class CountData:
    nominations: int = 0
    ballot_count: int = 0
    points: int = 0


class StepRecorder(Protocol):
    def __call__(
        self,
        ballots: NominatingBallots,
        counts: dict[str, CountData],
        eliminations: list[str],
    ) -> None: ...


def null_recorder(
    ballots: NominatingBallots,
    counts: dict[str, CountData],
    eliminations: list[str],
) -> None:
    pass


def eliminate_works(
    ballots: NominatingBallots, eliminations: list[str]
) -> NominatingBallots:
    eliminations_set = set(eliminations)
    cleaned_ballots = [
        Counter({w: n for w, n in ballot.items() if w not in eliminations_set})
        for ballot in ballots
    ]
    return [ballot for ballot in cleaned_ballots if len(ballot) > 0]


def eph(
    # Each ballot is one member's nominations, keyed by work with the number of times
    # they wrote it down.
    ballots: NominatingBallots,
    finalist_count: int = 6,
    record_steps: StepRecorder = null_recorder,
):
    """Implement the EPH ballot construction algorithm."""
    nominating = list(ballots)

    while len(nominating) > 0:
        counts = count_nominations(nominating)
        eliminations = nominations_for_elimination(counts)
        next_size = len(counts) - len(eliminations)
        record_steps(
            nominating, counts, [] if next_size < finalist_count else eliminations
        )
        if next_size == finalist_count:
            finalist_names = [
                work for work in counts.keys() if work not in eliminations
            ]
            # Record a final step with only the finalists and their redistributed
            # scores, so auditors can verify the full point redistribution.
            finalist_ballots = eliminate_works(nominating, eliminations)
            finalist_counts = count_nominations(finalist_ballots)
            record_steps(finalist_ballots, finalist_counts, [])
            return finalist_names

        if next_size < finalist_count:
            return list(counts.keys())

        nominating = eliminate_works(nominating, eliminations)


def count_nominations(ballots: NominatingBallots) -> dict[str, CountData]:
    points_per_ballot = (
        60  # chosen because it means we don't need to deal with floating-point math.
    )
    counts: dict[str, CountData] = {}
    for ballot in ballots:
        divisor = len(ballot)
        nomination_points = points_per_ballot // divisor

        for work, written_down in ballot.items():
            count = counts.get(work)
            if count is None:
                count = CountData()
                counts[work] = count

            count.nominations += written_down
            count.ballot_count += 1
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
    fewest_nominations = min(
        counts.values(), key=attrgetter("ballot_count")
    ).ballot_count
    fewest = {
        work: count
        for work, count in counts.items()
        if count.ballot_count == fewest_nominations
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


def all_min(iterable, key=lambda x: x) -> list:
    """Return a list of all items in the iterable that are tied for minimum value."""
    sorted_items = sorted(iterable, key=key)
    min_value = key(sorted_items[0])
    return [item for item in sorted_items if key(item) == min_value]

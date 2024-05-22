from dataclasses import dataclass, field
from itertools import takewhile

import pyrankvote
import pyrankvote.helpers
from django.utils.safestring import mark_safe
from nomnom.convention import HugoAwards
from wsfs.rules.constitution_2023 import ballots_from_category

from nominate import models


def get_results_for_election(
    awards: HugoAwards, election: models.Election
) -> dict[models.Category, pyrankvote.helpers.ElectionResults]:
    category_results: dict[models.Category, pyrankvote.helpers.ElectionResults] = {}
    for c in election.category_set.all():
        election_ballots = ballots_from_category(c)
        maybe_no_award = [c for c in c.finalist_set.all() if c.name == "No Award"]
        if maybe_no_award:
            no_award = pyrankvote.Candidate(str(maybe_no_award[0]))
        else:
            no_award = None

        category_results[c] = awards.counter(
            ballots=election_ballots.ballots,
            candidates=election_ballots.candidates,
            runoff_candidate=no_award,
        )

    return category_results


@dataclass
class VPR:
    votes: str | None
    eliminated: bool = False
    winner: bool = False
    won: bool = False

    def __str__(self):
        return self.votes if self.votes else mark_safe("&nbsp;")

    @property
    def extra_class(self) -> str:
        class_list = []
        if self.winner:
            class_list.append("winner")

        if self.eliminated:
            class_list.append("eliminated")

        if self.won:
            class_list.append("won")

        return " ".join(class_list)


@dataclass
class CandidateResults:
    candidate: str
    votes_per_round: list[float | None] = field(default_factory=list)
    won: bool = False

    @property
    def float_format(self) -> str:
        all_integers = all(v is None or v.is_integer() for v in self.votes_per_round)
        return ".0f" if all_integers else ".2f"

    def votes_per_round_details(self) -> list[VPR | None]:
        return [
            VPR(
                votes=f"{v:{self.float_format}}" if v is not None else None,
                eliminated=(
                    not self.won
                    and (i == self.rounds - 1 or i == len(self.votes_per_round) - 1)
                ),
                winner=self.won,
                won=self.won and i >= len(self.votes_per_round) - 2,
            )
            for i, v in enumerate(self.votes_per_round)
        ]

    @property
    def rounds(self) -> int:
        # the only votes we count are all the votes in votes_per_round before the first None value
        valid_votes = list(takewhile(lambda x: x is not None, self.votes_per_round))
        return len(valid_votes)

    @property
    def sort_key(self) -> int:
        # bump up the winner a bit
        if self.won and self.candidate != "No Award":
            return self.rounds + 1
        return self.rounds


def result_to_slant_table(
    results: list[pyrankvote.helpers.RoundResult],
) -> list[CandidateResults]:
    candidate_results: dict[str, CandidateResults] = {}

    main_results = results[:-1]

    # we rely on the fact that the results are in order of rounds, so all candidates are in the
    # first round, to set up our candidate list,
    for candidate in results[0].candidate_results:
        candidate_results[candidate.candidate.name] = CandidateResults(
            candidate.candidate.name
        )

    # now we can add the votes to the candidate_results. We omit the
    # final round which is the No Award runoff.
    for result in main_results:
        for candidate in result.candidate_results:
            if candidate.number_of_votes > 0:
                candidate_results[candidate.candidate.name].votes_per_round.append(
                    candidate.number_of_votes
                )

    # Let's add the runoff state; we fill in the blanks on the runoff votes, first:
    try:
        no_award = candidate_results["No Award"]
        cn = list(
            sorted(
                candidate_results.values(),
                key=lambda cr: cr.votes_per_round[-1],
                reverse=True,
            )
        )[0]
        winner = candidate_results[cn.candidate]
        no_award.votes_per_round.extend(
            [None] * (len(winner.votes_per_round) - len(no_award.votes_per_round))
        )

        last = results[-1]
        results_by_candidate: dict[str, pyrankvote.helpers.CandidateResult] = {
            c.candidate.name: c for c in last.candidate_results
        }
        winner.votes_per_round.append(
            results_by_candidate[winner.candidate].number_of_votes
        )
        no_award.votes_per_round.append(
            results_by_candidate[no_award.candidate].number_of_votes
        )

    except KeyError:
        # This should never happen
        raise RuntimeError("Election counted without No Award")

    last_round = results[-1]
    winners = [
        cr.candidate
        for cr in last_round.candidate_results
        if cr.status == pyrankvote.helpers.CandidateStatus.Elected
    ]
    for candidate in winners:
        candidate_results[candidate.name].won = True

    values = list(candidate_results.values())
    values.sort(key=lambda cr: cr.sort_key, reverse=True)

    return values

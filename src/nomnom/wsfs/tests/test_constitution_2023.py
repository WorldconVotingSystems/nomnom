from typing import Set

import pytest
from pyrankvote import Ballot, Candidate
from pyrankvote.helpers import CandidateStatus

from nomnom.wsfs.rules.constitution_2023 import hugo_voting

ELECTION_DATA = {
    "candidates": [
        "Noah Ward",
        "Jean-Luc Picard",
        "Ellen Ripley",
        "Kara Thrace",
        "James T. Kirk",
        "Leia Organa",
    ],
    "ballots": [
        [
            "Ellen Ripley",
            "Noah Ward",
            "Kara Thrace",
            "Leia Organa",
            "James T. Kirk",
            "Jean-Luc Picard",
        ],
        [
            "James T. Kirk",
            "Leia Organa",
            "Ellen Ripley",
            "Noah Ward",
            "Jean-Luc Picard",
            "Kara Thrace",
        ],
        ["Noah Ward", "Jean-Luc Picard", "Leia Organa", "Ellen Ripley"],
        [
            "Jean-Luc Picard",
            "Leia Organa",
            "James T. Kirk",
            "Noah Ward",
            "Kara Thrace",
            "Ellen Ripley",
        ],
        ["Kara Thrace", "Noah Ward", "Leia Organa", "James T. Kirk", "Ellen Ripley"],
        [
            "Jean-Luc Picard",
            "Kara Thrace",
            "James T. Kirk",
            "Ellen Ripley",
            "Noah Ward",
        ],
        ["Leia Organa", "Jean-Luc Picard", "Ellen Ripley", "Noah Ward", "Kara Thrace"],
        [
            "James T. Kirk",
            "Noah Ward",
            "Jean-Luc Picard",
            "Leia Organa",
            "Ellen Ripley",
        ],
        ["Noah Ward", "Kara Thrace", "James T. Kirk", "Jean-Luc Picard", "Leia Organa"],
    ],
}


@pytest.fixture(name="candidates")
def get_candidates():
    return [Candidate(candidate) for candidate in ELECTION_DATA["candidates"]]


@pytest.fixture(name="ballots")
def get_ballots():
    return [
        Ballot([Candidate(candidate) for candidate in ballot])
        for ballot in ELECTION_DATA["ballots"]
    ]


@pytest.fixture(name="results")
def get_results(candidates, ballots):
    return hugo_voting(candidates, ballots)


def test_hugo_voting_no_candidates():
    with pytest.raises(RuntimeError):
        hugo_voting([], []).get_winners()


def test_hugo_voting_no_ballots():
    candidates = [Candidate("Candidate 1"), Candidate("Candidate 2")]
    res = hugo_voting(
        candidates,
        [],
    )

    print(res)
    assert all(c in res.get_winners() for c in candidates)


def test_hugo_voting_single_candidate_winner():
    candidate = Candidate("Winner")
    candidates = [candidate]
    ballots = [Ballot([candidate])]
    results = hugo_voting(candidates, ballots)
    print(results)
    assert results.get_winners() == [candidate]


def test_hugo_voting_multiple_candidates_winner(results):
    print(results)
    assert Candidate("Noah Ward") in results.get_winners()


class TestEdgeCases:
    def test_three_way_tie_should_not_eliminate(self):
        """When all remaining candidates are tied, none should be eliminated.

        Regression test: with 7 candidates where D, E, F, and No Award have no
        first-choice votes and get eliminated in early rounds, candidates A, B, and
        C each end up with 11 votes. The algorithm should recognize this as a
        three-way tie with all three remaining Hopeful, but instead incorrectly
        rejects one of them.

        This setup will result in 3 rounds:
        1. the candidates with no votes are eliminated. A, B, and C are "Hopeful"
        2. A, B, and C would be eliminated, but because that would clear the ballots, they are all elected instead
        3. Runoff with A, B, and C against "No Award"
        """
        a = Candidate("Candidate A")
        b = Candidate("Candidate B")
        c = Candidate("Candidate C")
        d = Candidate("Candidate D")
        e = Candidate("Candidate E")
        f = Candidate("Candidate F")
        no_award = Candidate("No Award")

        candidates = [a, b, c, d, e, f, no_award]

        # 33 ballots: 11 each ranking only A, B, or C.
        # D, E, F, and No Award receive no votes and are eliminated in rounds 1-4.
        # After those eliminations, A/B/C are tied at 11 votes each with 0
        # transferable votes remaining (all other ballots are exhausted).
        ballots = (
            [Ballot([a]) for _ in range(11)]
            + [Ballot([b]) for _ in range(11)]
            + [Ballot([c]) for _ in range(11)]
        )

        results = hugo_voting(candidates, ballots, runoff_candidate=no_award)

        # Find the last non-runoff round where only A, B, C have votes.
        # After D, E, F, and No Award are eliminated, the next round should show
        # all three tied candidates as Hopeful — none should be arbitrarily rejected.
        rounds = results.rounds

        # debugging
        for r in rounds:
            print(r)

        assert len(rounds) == 3, "Unexpected number of rounds"

        elected_round = rounds[1]
        hopeful_round = rounds[0]

        hopeful = [
            cr.candidate
            for cr in hopeful_round.candidate_results
            if cr.status == CandidateStatus.Hopeful
        ]
        assert set(hopeful) == {a, b, c}, f"Unexpected hopeful candidates: {hopeful}"

        elected = [
            cr.candidate
            for cr in elected_round.candidate_results
            if cr.status == CandidateStatus.Elected
        ]
        assert set(elected) == {a, b, c}, f"Unexpected elected candidates: {elected}"

        # All three should have 11 votes
        for cr in elected_round.candidate_results:
            if cr.candidate in (a, b, c):
                assert cr.number_of_votes == 11, (
                    f"Unexpected vote count for {cr.candidate}"
                )

    def test_when_tied_for_elimination_use_first_place_votes_as_tiebreaker(self):
        """Don't eliminate all bottom candidates automatically.

        When candidates are tied for elimination, the candidate with the fewest first-place votes
        should be eliminated.

        """
        a = Candidate("Candidate A")
        b = Candidate("Candidate B")
        c = Candidate("Candidate C")
        d = Candidate("Candidate D")
        e = Candidate("Candidate E")
        f = Candidate("Candidate F")
        no_award = Candidate("No Award")

        candidates = [a, b, c, d, e, f, no_award]

        # Craft a scenario where the two candidates with the fewest votes are tied, but one has fewer first-place votes and should be eliminated.
        # In this case, after eliminating a candidate, two are now tied with their votes transferred, but the tiebreaker should still be applied correctly.
        # So, we need realistic ballots that would lead to this scenario:
        ballots = [
            *[Ballot([a]) for _ in range(6)],  # A: 6 first-place
            *[Ballot([b]) for _ in range(5)],  # B: 5 first-place
            *[Ballot([c]) for _ in range(4)],  # C: 4 first-place
            *[Ballot([e]) for _ in range(3)],  # E: 3 first-place (no transfers)
            *[Ballot([d]) for _ in range(2)],  # D: 2 first-place (no transfers)
            Ballot([f, d]),  # F: 1 first-place, transfers to D
            # No Award: 0 first-place
        ]
        results = hugo_voting(candidates, ballots, runoff_candidate=no_award)

        # No award is eliminated first,then D; the next round is our test round.
        elimination_round = results.rounds[2]

        def rejected(round) -> Set[Candidate]:
            return set(
                cr.candidate
                for cr in round.candidate_results
                if cr.status == CandidateStatus.Rejected
            )

        ignored_eliminations = rejected(results.rounds[0]) | rejected(results.rounds[1])
        assert rejected(elimination_round) - ignored_eliminations == {d}, (
            f"Unexpected rejected candidates: {rejected(elimination_round)}"
        )

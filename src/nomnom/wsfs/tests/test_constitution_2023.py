from typing import Set

import pytest
from pyrankvote import Ballot, Candidate
from pyrankvote.helpers import CandidateStatus

from nomnom.wsfs.rules.constitution_2023 import NoFinalists, hugo_voting

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
    with pytest.raises(NoFinalists):
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

    def test_no_award_wins_the_runoff(self):
        """No Award can beat the winner of the count in the final runoff.

        The minimal case: Candidate A survives the instant-runoff count, but a
        majority of the voters ranked No Award above A.

            Voter 1: A, No Award
            Voter 2: A, No Award
            Voter 3: B, No Award
            Voter 4: C, No Award
            Voter 5: No Award

        In the count, B, C and No Award are tied for last place with one
        first-preference vote each, so all three are eliminated together; none
        of their ballots have a surviving preference to transfer, which leaves A
        as the only candidate in the race and the winner of the count. In the
        runoff, No Award is ranked above A on three of the five ballots, so no
        award is granted in the category.
        """
        a = Candidate("Candidate A")
        b = Candidate("Candidate B")
        c = Candidate("Candidate C")
        no_award = Candidate("No Award")

        candidates = [a, b, c, no_award]

        ballots = [
            Ballot([a, no_award]),
            Ballot([a, no_award]),
            Ballot([b, no_award]),
            Ballot([c, no_award]),
            Ballot([no_award]),
        ]

        results = hugo_voting(candidates, ballots, runoff_candidate=no_award)

        # debugging
        for r in results.rounds:
            print(r)

        # One counting round (B, C and No Award are tied for last and eliminated,
        # leaving A to fill the only seat) plus the runoff.
        assert len(results.rounds) == 2, "Unexpected number of rounds"

        count_round, runoff_round = results.rounds

        def elected(election_round) -> Set[Candidate]:
            return set(
                cr.candidate
                for cr in election_round.candidate_results
                if cr.status == CandidateStatus.Elected
            )

        def votes(election_round, candidate) -> int:
            # pyrankvote tallies in floating point, but every ballot here is a
            # whole vote; round to int so the assertions below don't compare an
            # int to a float.
            return round(
                next(
                    cr.number_of_votes
                    for cr in election_round.candidate_results
                    if cr.candidate == candidate
                )
            )

        # Candidate A survives the count...
        assert elected(count_round) == {a}, "Candidate A should win the count"

        # ... but loses the runoff to No Award, 3 votes to 2.
        assert elected(runoff_round) == {no_award}, "No Award should win the runoff"
        assert votes(runoff_round, no_award) == 3
        assert votes(runoff_round, a) == 2

        assert results.get_winners() == [no_award]

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

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Constitution §6.5: the runoff test should be skipped 'unless the "
            "run-off candidate shall be the sole winner'. Current code "
            "unconditionally appends a runoff round whenever a runoff_candidate "
            "is provided, even when No Award is itself the tentative winner."
        ),
    )
    def test_no_runoff_when_no_award_is_sole_winner(self):
        """§6.5: skip the runoff when No Award is the tentative winner.

        If No Award wins outright via the §6.4 IRV process, the §6.5 runoff
        test is moot and should not be performed. The result set should
        therefore contain only the IRV rounds, with no trailing runoff round.
        """
        a = Candidate("Candidate A")
        b = Candidate("Candidate B")
        no_award = Candidate("No Award")

        candidates = [a, b, no_award]

        # No Award gets an outright majority of first-place votes.
        ballots = [
            *[Ballot([no_award]) for _ in range(5)],
            *[Ballot([a]) for _ in range(2)],
            *[Ballot([b]) for _ in range(2)],
        ]

        results = hugo_voting(candidates, ballots, runoff_candidate=no_award)

        assert results.get_winners() == [no_award]

        # No Award meets the majority threshold (5 of 9) on the very first
        # tally, so the §6.4 IRV process completes in a single round. Per
        # §6.5 the runoff test is skipped because the runoff candidate is
        # the sole tentative winner, so no extra round should be appended.
        assert len(results.rounds) == 1, (
            f"Expected exactly 1 round (single IRV tally, no runoff); "
            f"got {len(results.rounds)}. An extra round indicates the "
            f"§6.5 runoff was performed when it should have been skipped."
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Constitution §3.12.1: when all remaining finalists are tied, "
            "'no tie-breaking shall be done' and the finalists excluding "
            "No Award shall be declared joint winners. Current code applies "
            "the §6.4 first-place-votes tiebreaker even when all remaining "
            "candidates are tied on current vote count, and eliminates the "
            "one with fewest original first-place votes instead of declaring "
            "joint winners."
        ),
    )
    def test_all_tied_on_votes_but_differ_on_first_place_should_be_joint_winners(self):
        """§3.12.1: 'all remaining finalists are tied' means tied on votes.

        Scenario: after No Award and one low-vote candidate are eliminated,
        A, B, and C are all tied at 3 current votes. They differ on original
        first-place votes (A=3, B=3, C=2). §3.12.1 says no tie-breaking is
        to be done and all three should be joint winners.

        The current implementation only treats them as all-tied when the
        first-place tiebreak also fails to separate them, so C ends up
        eliminated.
        """
        a = Candidate("Candidate A")
        b = Candidate("Candidate B")
        c = Candidate("Candidate C")
        e = Candidate("Candidate E")
        no_award = Candidate("No Award")

        candidates = [a, b, c, e, no_award]

        # Round 1: A=3, B=3, C=2, E=1, NA=0 -> NA eliminated
        # Round 2: A=3, B=3, C=2, E=1       -> E eliminated, transfers to C
        # Round 3: A=3, B=3, C=3            -> all tied on current votes
        #                                      but original first-place is
        #                                      A=3, B=3, C=2.
        ballots = [
            *[Ballot([a]) for _ in range(3)],
            *[Ballot([b]) for _ in range(3)],
            *[Ballot([c]) for _ in range(2)],
            Ballot([e, c]),
        ]

        results = hugo_voting(candidates, ballots, runoff_candidate=no_award)

        winners = set(results.get_winners())
        assert winners == {a, b, c}, (
            f"Expected joint winners {{A, B, C}}, got {winners}. "
            f"§3.12.1 requires no tie-breaking when all remaining finalists "
            f"are tied on votes."
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Constitution §3.12.1: when all remaining finalists are tied, "
            "'the finalists excluding No Award shall be declared joint "
            "winners'. Current code's punt-to-runoff branch elects every "
            "remaining finalist, including No Award, in the joint-election "
            "round. A subsequent §6.5 runoff usually removes No Award from "
            "the final winner set, but the intermediate round still shows "
            "No Award as elected, which is constitutionally incorrect."
        ),
    )
    def test_all_tied_joint_winners_should_exclude_no_award(self):
        """§3.12.1: No Award is never a joint winner of an all-tied round.

        When the punt-to-runoff branch fires because every remaining finalist
        (including No Award) is tied for elimination, No Award should not
        appear in the Elected column of that round at all.
        """
        a = Candidate("Candidate A")
        b = Candidate("Candidate B")
        c = Candidate("Candidate C")
        no_award = Candidate("No Award")

        candidates = [a, b, c, no_award]

        # Three candidates each receive 1 first-place vote; No Award receives
        # 1 first-place vote as well. All four are tied at 1 vote with no
        # transfers possible, triggering the punt-to-runoff branch.
        ballots = [
            Ballot([a]),
            Ballot([b]),
            Ballot([c]),
            Ballot([no_award]),
        ]

        results = hugo_voting(candidates, ballots, runoff_candidate=no_award)

        # Round structure on the punt-to-runoff path is deterministic:
        # rounds[0] is the joint-election round, rounds[1] is the §6.5 runoff
        # appended afterward. The joint-election round is the one we care
        # about: per §3.12.1 No Award must not appear as Elected there.
        assert len(results.rounds) == 2, (
            f"Expected 2 rounds (joint election + runoff); got {len(results.rounds)}"
        )
        joint_round = results.rounds[0]

        elected_in_joint_round = {
            cr.candidate
            for cr in joint_round.candidate_results
            if cr.status == CandidateStatus.Elected
        }
        assert {a, b, c}.issubset(elected_in_joint_round), (
            f"Expected A, B, C to be jointly elected; elected: {elected_in_joint_round}"
        )
        assert no_award not in elected_in_joint_round, (
            f"No Award should not be elected in the joint-winners round; "
            f"§3.12.1 says joint winners exclude No Award. "
            f"Elected in this round: {elected_in_joint_round}"
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Constitution §6.5 is written in terms of a singular 'tentative "
            "winner', and the natural reading when multiple tentative winners "
            "exist is to run a separate pairwise comparison for each one "
            "against the runoff candidate. Current code bundles all tentative "
            "winners and the runoff candidate into a single truncated-ballot "
            "tally and compares votes(runoff_candidate) > votes(winners[0]), "
            "which is a plurality vote among the three rather than two "
            "separate pairwise comparisons. The outcome rarely differs in "
            "practice, but the round structure does."
        ),
    )
    def test_joint_winners_runoff_compares_each_winner_separately(self):
        """§6.5: with joint winners, run pairwise runoffs separately.

        When §3.12.1 produces joint tentative winners {A, B}, the §6.5
        text 'unless the run-off candidate shall be the sole winner, the
        following additional test shall be made' is naturally read as
        running the test for each tentative winner: A vs No Award, then
        B vs No Award. The current implementation bundles them into a
        single plurality tally instead, which is a different operation.

        This test asserts the round shape that would result from running
        separate pairwise comparisons: one runoff round per tentative
        winner, appended after the joint-election round.
        """
        a = Candidate("Candidate A")
        b = Candidate("Candidate B")
        no_award = Candidate("No Award")

        candidates = [a, b, no_award]

        # Construct joint tentative winners A and B via the punt-to-runoff
        # branch. Each ballot expresses a preference between its top choice
        # and No Award so the pairwise comparisons are well-defined.
        #   3 ballots:  A > NA       -> A first-place, A preferred over NA
        #   3 ballots:  B > NA       -> B first-place, B preferred over NA
        # Round 1: A=3, B=3, NA=0. NA last, eliminated, no transfers.
        # Round 2: A=3, B=3. Tied. Punt-to-runoff elects A and B jointly.
        ballots = [
            *[Ballot([a, no_award]) for _ in range(3)],
            *[Ballot([b, no_award]) for _ in range(3)],
        ]

        results = hugo_voting(candidates, ballots, runoff_candidate=no_award)

        # Expected structure under the per-winner-pairwise reading:
        #   rounds[0]: IRV round eliminating No Award
        #   rounds[1]: joint election of A and B
        #   rounds[2]: pairwise runoff of A vs No Award
        #   rounds[3]: pairwise runoff of B vs No Award
        # Current code produces only 3 rounds (one bundled runoff).
        assert len(results.rounds) == 4, (
            f"Expected 4 rounds (2 IRV + 2 separate pairwise runoffs); "
            f"got {len(results.rounds)}. §6.5 should run one pairwise "
            f"comparison per tentative winner against No Award."
        )

        # Both A and B should win their individual pairwise comparisons here
        # (3 ballots prefer each over No Award; 0 prefer No Award over them).
        winners = set(results.get_winners())
        assert winners == {a, b}, f"Expected joint winners {{A, B}}; got {winners}"

    def test_eliminate_together_when_first_place_tiebreak_also_ties(self):
        """§6.4: when tied candidates are also tied on first-place votes,
        all such candidates shall be eliminated together.

        Complement to test_when_tied_for_elimination_use_first_place_votes_as_tiebreaker,
        which checks that the §6.4 first-place tiebreak singles out a loser
        when the original first-place counts differ. This test checks the
        other half of the rule: when the tiebreak fails to separate them,
        all tied candidates are eliminated in the same round.
        """
        a = Candidate("Candidate A")
        b = Candidate("Candidate B")
        c = Candidate("Candidate C")
        d = Candidate("Candidate D")
        e = Candidate("Candidate E")
        f = Candidate("Candidate F")
        no_award = Candidate("No Award")

        candidates = [a, b, c, d, e, f, no_award]

        # Original first-place tallies:
        #   A: 5, B: 4, C: 2, D: 2, E: 1 (transfers to C), F: 1 (transfers to D)
        # Round 1: No Award (0) eliminated; no transfers.
        # Round 2: E and F tied at 1 vote each. First-place tiebreak: both at 1.
        #          Tied on both criteria -> both eliminated together. E
        #          transfers to C, F transfers to D.
        # Round 3: A=5, B=4, C=3, D=3. C and D tied for last at 3 votes. Their
        #          original first-place counts are also tied (both at 2), so
        #          they must be eliminated together per §6.4.
        ballots = [
            *[Ballot([a]) for _ in range(5)],
            *[Ballot([b]) for _ in range(4)],
            *[Ballot([c]) for _ in range(2)],
            *[Ballot([d]) for _ in range(2)],
            Ballot([e, c]),
            Ballot([f, d]),
        ]

        results = hugo_voting(candidates, ballots, runoff_candidate=no_award)

        def rejected(round):
            return {
                cr.candidate
                for cr in round.candidate_results
                if cr.status == CandidateStatus.Rejected
            }

        prior = rejected(results.rounds[0]) | rejected(results.rounds[1])
        round_3_new_rejections = rejected(results.rounds[2]) - prior
        assert round_3_new_rejections == {c, d}, (
            f"Expected round 3 to eliminate C and D together (tied on votes "
            f"and on first-place votes per §6.4); got {round_3_new_rejections}"
        )

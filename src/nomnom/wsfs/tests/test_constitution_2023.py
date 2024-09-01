import pytest
from pyrankvote import Ballot, Candidate

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

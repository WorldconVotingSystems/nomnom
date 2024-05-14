import pyrankvote
from nomnom.convention import HugoAwards
from wsfs.rules.constitution_2023 import ballots_from_category

from nominate import models


def get_results_for_election(awards: HugoAwards, election: models.Election):
    category_results = {}
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

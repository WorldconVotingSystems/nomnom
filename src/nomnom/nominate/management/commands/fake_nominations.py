import random

import djclick as click

from nomnom.nominate.factories import NominationFactory
from nomnom.nominate.models import Election, NominatingMemberProfile


@click.command()
@click.argument("election_id")
@click.argument("ballots", default=5, type=int)
def main(election_id: str, ballots: int):
    election = Election.objects.get(slug=election_id)
    possible_nominators = {n.pk: n for n in NominatingMemberProfile.objects.all()}
    nominator_ids = random.sample([n for n in possible_nominators], ballots)
    nominators = [possible_nominators[pk] for pk in nominator_ids]

    for category in election.category_set.all():
        for nominator in nominators:
            # assume each nominator nominates 5 works
            NominationFactory.create_batch(5, nominator=nominator, category=category)

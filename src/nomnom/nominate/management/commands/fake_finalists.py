import djclick as click
from nomnom.nominate.factories import FinalistFactory
from nomnom.nominate.models import Election


@click.command()
@click.argument("election_id")
@click.argument("finalist_count", default=5, type=int)
def main(election_id: str, finalist_count: int):
    election = Election.objects.get(slug=election_id)
    for category in election.category_set.all():
        finalists = category.finalist_set.all()
        finalists_to_create = 6 - len(finalists)
        if any(f.name == "No Award" for f in finalists):
            finalists_to_create -= 1
        else:
            FinalistFactory.create(category=category, name="No Award")

        FinalistFactory.create_batch(category=category, size=finalists_to_create)

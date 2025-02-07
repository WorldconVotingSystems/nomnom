import djclick as click
from nomnom.nominate.factories import CategoryFactory, FinalistFactory
from nomnom.nominate.models import Election


@click.command()
@click.argument("election_id")
@click.argument("finalist_count", default=5, type=int)
def main(election_id: str, finalist_count: int):
    election = Election.objects.get(slug=election_id)
    cat = CategoryFactory.create(election=election)
    print(f"Created category for {election.name}")

    for i in range(finalist_count):
        FinalistFactory.create(category=cat, ballot_position=i + 1)
        print(f"Created finalist {i + 1} for {cat.name}")

    FinalistFactory.create(
        category=cat, ballot_position=finalist_count + 1, name="No Award"
    )

import djclick as click
from tenacity import Retrying, stop_after_attempt

from nomnom.nominate.factories import NominatingMemberProfileFactory
from nomnom.nominate.models import NominatingMemberProfile


@click.command()
@click.argument("nominator_id", nargs=-1)
def command_name(nominator_id: list[str]):
    nominator_ids = [int(n) for n in nominator_id]
    existing_nominator_ids = NominatingMemberProfile.objects.filter(
        id__in=nominator_ids
    ).values_list("id", flat=True)

    missing_id_list = [i for i in nominator_ids if i not in existing_nominator_ids]

    for i in missing_id_list:
        for attempt in Retrying(stop=stop_after_attempt(3)):
            with attempt:
                NominatingMemberProfileFactory(id=i)
        new_nominator = NominatingMemberProfile.objects.get(id=i)

        print(
            f"Created profile {i}, {new_nominator.display_name} (user={new_nominator.user.username})"
        )

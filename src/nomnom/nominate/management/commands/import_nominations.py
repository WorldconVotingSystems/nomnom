import csv
import uuid
from datetime import datetime

import djclick as click
import icecream
from django.contrib.auth import get_user_model
from django.db import transaction

from nomnom.nominate.models import (
    Category,
    Election,
    NominatingMemberProfile,
    Nomination,
)

icecream.install()

NAMESPACE_NOMNOM = uuid.UUID(hex="11ae714b909c41abb660757e788a50b8")


@click.command()
@click.argument("election-id")
@click.argument("nomination-export-file", type=click.File("r"))
@click.option("--purge", is_flag=True, default=False)
def main(election_id, nomination_export_file, purge=False):
    election = Election.objects.get(slug=election_id)
    UserModel = get_user_model()

    with transaction.atomic():
        categories = election.category_set.all()
        category_lookup: dict[str, Category] = {c.name: c for c in categories}

        if purge:
            Nomination.objects.filter(category__election=election).delete()

        reader = csv.DictReader(nomination_export_file)

        rows = list(reader)

        for idx, row in enumerate(rows):
            f1 = row["field_1"]
            f2 = row["field_2"]
            f3 = row["field_3"]
            nominator_name = row["nominator"]
            nomination_date = datetime.fromisoformat(row["nomination_date"])
            category_name = row["category"]
            nomination_ip_address = row["nomination_ip_address"]

            # we want a stable name mapping for the nominators; we'll use
            # a UUID generated from the nominator_name,id
            username = f"import-{uuid.uuid3(NAMESPACE_NOMNOM, f'{nominator_name}')}"
            user, created = UserModel.objects.get_or_create(
                username=username,
            )

            try:
                user.convention_profile
            except NominatingMemberProfile.DoesNotExist:
                user.convention_profile = NominatingMemberProfile.objects.create(
                    user=user,
                    preferred_name=f"Import {idx}",
                    member_number=f"import.{idx}",
                )

            ip_address = nomination_ip_address

            category = category_lookup.get(category_name)

            if category is None:
                category = Category.objects.create(
                    name=category_name,
                    election=election,
                    ballot_position=categories.count(),
                )
                category_lookup[category_name] = category

            Nomination.objects.create(
                nominator=user.convention_profile,
                category=category,
                field_1=f1,
                field_2=f2,
                field_3=f3,
                nomination_ip_address=ip_address,
                nomination_date=nomination_date,
            )

    print(f"Imported nominations for {election.name}")

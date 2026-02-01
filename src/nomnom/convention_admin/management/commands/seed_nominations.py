"""
Management command to seed nominations with realistic variations for a Hugo Awards election.

Creates members and nominations using sample works from seed_data, with variations
to simulate real-world typos and misspellings.
"""

import random

import djclick as click
from django.contrib.auth import get_user_model
from django.db import transaction
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)

from nomnom.convention_admin.management.commands._seed_base import suppress_sql_logging
from nomnom.convention_admin.seed_data.sample_works import get_samples_for_category_name
from nomnom.convention_admin.utils import (
    WorkSelector,
    VariationGenerator,
    select_random_ip,
)
from nomnom.nominate.models import (
    Category,
    Election,
    Nomination,
    NominatingMemberProfile,
)

UserModel = get_user_model()


# Category participation rates (fraction of members who nominate in each type)
MAJOR_FICTION_CATEGORIES = {
    "Best Novel",
    "Best Novella",
    "Best Novelette",
    "Best Short Story",
}

MAJOR_PARTICIPATION = (0.70, 0.90)  # 70-90% of members
OTHER_PARTICIPATION = (0.40, 0.60)  # 40-60% of members


def get_participation_rate(category_name: str) -> float:
    """Get the participation rate for a category."""
    if category_name in MAJOR_FICTION_CATEGORIES:
        return random.uniform(*MAJOR_PARTICIPATION)
    return random.uniform(*OTHER_PARTICIPATION)


def create_member(member_index: int) -> NominatingMemberProfile:
    """Create a member with user account."""
    # Create user
    username = f"member{member_index:04d}"
    email = f"{username}@example.com"

    user = UserModel.objects.create_user(
        username=username,
        email=email,
        password="password123",  # Not used in seeding context
        first_name="Member",
        last_name=f"{member_index}",
    )

    # Create member profile
    member = NominatingMemberProfile.objects.create(
        user=user,
        preferred_name=f"Member {member_index}",
        member_number=f"{member_index:05d}",
    )

    return member


def create_nominations_for_member(
    member: NominatingMemberProfile,
    category: Category,
    sample_works: list[dict],
) -> int:
    """
    Create nominations for a single member in a single category.

    Returns the number of nominations created.
    """
    if not sample_works:
        return 0

    # Select works for this member to nominate
    selector = WorkSelector(sample_works)
    num_nominations = random.randint(3, 5)  # Each member nominates 3-5 works
    selected_works = selector.select_works_for_member(num_nominations)

    # Generate variations and create nominations
    variation_generator = VariationGenerator()
    ip_address = select_random_ip()
    nominations_created = 0

    for work_data in selected_works:
        # Get canonical or variation
        work = variation_generator.select_variation(work_data)

        # Extract fields based on category field count
        field_1 = work.get("field_1", "")
        field_2 = work.get("field_2", "") if category.fields >= 2 else ""
        field_3 = work.get("field_3", "") if category.fields >= 3 else ""

        # Skip if required fields are missing
        if not field_1:
            continue
        if category.fields >= 2 and category.field_2_required and not field_2:
            continue
        if category.fields >= 3 and category.field_3_required and not field_3:
            continue

        Nomination.objects.create(
            nominator=member,
            category=category,
            field_1=field_1,
            field_2=field_2,
            field_3=field_3,
            nomination_ip_address=ip_address,
        )
        nominations_created += 1

    return nominations_created


@click.command()
@click.argument("election_slug")
@click.option(
    "--count",
    "-c",
    default=100,
    type=int,
    help="Number of members to create (default: 100)",
)
@click.option(
    "--categories",
    "-cat",
    multiple=True,
    help="Specific category names to seed (can be specified multiple times). If not provided, seeds all categories.",
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear existing nominations before seeding",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be created without actually creating it",
)
def main(
    election_slug: str,
    count: int,
    categories: tuple[str, ...],
    clear: bool,
    dry_run: bool,
):
    """
    Seed nominations for an election with realistic variations.

    Creates members and their nominations using sample works with variations
    to simulate real-world nomination data.

    Example:
        python manage.py seed_nominations 2025-hugos --count 100
        python manage.py seed_nominations 2025-hugos --count 50 --categories "Best Novel"
        python manage.py seed_nominations 2025-hugos --clear --count 100
    """
    console = Console()

    with suppress_sql_logging():
        # Load election
        try:
            election = Election.objects.get(slug=election_slug)
        except Election.DoesNotExist:
            console.print(f"[red]❌ Election '{election_slug}' not found[/red]")
            return

        console.print(
            f"[cyan bold]📊 Seeding nominations for: {election.name}[/cyan bold]"
        )

        # Get categories to seed
        if categories:
            category_queryset = election.category_set.filter(name__in=categories)
            missing = set(categories) - set(
                category_queryset.values_list("name", flat=True)
            )
            if missing:
                console.print(
                    f"[yellow]⚠️  Categories not found: {', '.join(missing)}[/yellow]"
                )
        else:
            category_queryset = election.category_set.all()

        categories_list = list(category_queryset)

        if not categories_list:
            console.print("[red]❌ No categories found to seed[/red]")
            return

        console.print(f"   Categories: {len(categories_list)}")
        console.print(f"   Members: {count}")

        if dry_run:
            console.print("\n[yellow]DRY RUN MODE - No changes will be made[/yellow]")
            console.print(
                f"\nWould create {count} members with nominations in {len(categories_list)} categories"
            )
            console.print("Sample categories:")
            for i, cat in enumerate(categories_list[:3], 1):
                console.print(f"  {i}. {cat.name}")
            if len(categories_list) > 3:
                console.print(f"  ... and {len(categories_list) - 3} more")
            # Estimate nominations
            estimated_noms = count * len(categories_list) * 4  # rough average
            console.print(f"\nEstimated nominations: ~{estimated_noms}")
            return

        # Clear existing nominations if requested
        if clear:
            with transaction.atomic():
                deleted_count = Nomination.objects.filter(
                    category__election=election
                ).delete()[0]
                console.print(
                    f"[yellow]🗑️  Cleared {deleted_count} existing nominations[/yellow]"
                )

        # Create members and nominations
        total_nominations = 0
        total_participating = 0

        with transaction.atomic():
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "[cyan]Creating members and nominations...", total=count
                )

                for i in range(1, count + 1):
                    # Create member
                    member = create_member(i)
                    member_nominations = 0

                    # For each category, decide if this member participates
                    for category in categories_list:
                        participation_rate = get_participation_rate(category.name)

                        # Skip this category with some probability
                        if random.random() > participation_rate:
                            continue

                        # Get sample works for this category
                        sample_works = get_samples_for_category_name(category.name)

                        if not sample_works:
                            continue

                        # Create nominations for this member in this category
                        nominations_created = create_nominations_for_member(
                            member, category, sample_works
                        )
                        member_nominations += nominations_created

                    total_nominations += member_nominations
                    if member_nominations > 0:
                        total_participating += 1

                    progress.update(task, advance=1)

        # Summary
        console.print()
        console.print("[green bold]✅ Seeding complete![/green bold]")
        console.print(f"   Total members created: {count}")
        console.print(f"   Members with nominations: {total_participating}")
        console.print(f"   Total nominations: {total_nominations}")
        console.print(
            f"   Avg nominations per participating member: {total_nominations / max(total_participating, 1):.1f}"
        )

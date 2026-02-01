"""Management command to create voting ballots (ranks) for an election.

This command generates realistic voting data by creating members who rank the finalists
in each category. It simulates the final voting phase of the Hugo Awards process.

Usage:
    python manage.py seed_ranks <election_slug> --count N [--clear] [--new-members]

Example:
    python manage.py seed_ranks worldcon-2025 --count 100 --clear --new-members
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
from nomnom.convention_admin.utils import select_random_ip
from nomnom.nominate.models import (
    Category,
    Election,
    Finalist,
    NominatingMemberProfile,
    Rank,
)

User = get_user_model()

# Realistic voting participation rates
CATEGORY_VOTE_PROBABILITY = 0.75  # 75% chance a voter votes in a given category
FINALIST_RANK_PROBABILITY = 0.85  # 85% chance a voter ranks a given finalist


def create_voting_member(
    member_number: int, election: Election
) -> NominatingMemberProfile:
    """Create a new voting member for the election.

    Args:
        member_number: Sequential member number
        election: Election to create member for

    Returns:
        NominatingMemberProfile for the new member
    """
    username = f"voter_{election.slug}_{member_number:04d}"
    email = f"{username}@example.com"

    user = User.objects.create_user(
        username=username,
        email=email,
        first_name="Voter",
        last_name=f"{member_number:04d}",
    )

    profile = NominatingMemberProfile.objects.create(
        user=user,
        member_number=f"V-{member_number:05d}",
    )

    return profile


def create_ballot(
    election: Election,
    member: NominatingMemberProfile,
    category_vote_probability: float = CATEGORY_VOTE_PROBABILITY,
    finalist_rank_probability: float = FINALIST_RANK_PROBABILITY,
) -> tuple[int, int]:
    """Create a voting ballot for a member.

    Args:
        election: Election to vote in
        member: Member casting the vote
        category_vote_probability: Probability of voting in each category
        finalist_rank_probability: Probability of ranking each finalist

    Returns:
        Tuple of (categories_voted, total_ranks_created)
    """
    categories_voted = 0
    total_ranks = 0

    for category in Category.objects.filter(election=election):
        # Decide whether to vote in this category
        if random.random() > category_vote_probability:
            continue

        finalists = list(category.finalist_set.all())
        if not finalists:
            continue  # Skip categories with no finalists

        # Shuffle finalists to randomize preference order
        random.shuffle(finalists)

        # Randomly select which finalists to rank
        selected_finalists = [
            f for f in finalists if random.random() < finalist_rank_probability
        ]

        # Create ranks with sequential positions
        for i, finalist in enumerate(selected_finalists):
            Rank.objects.create(
                membership=member,
                finalist=finalist,
                position=i + 1,
                voter_ip_address=select_random_ip(),
            )
            total_ranks += 1

        if selected_finalists:
            categories_voted += 1

    return categories_voted, total_ranks


@click.command()
@click.argument("election_slug")
@click.option(
    "--count", required=True, type=int, help="Number of voting members to create"
)
@click.option("--clear", is_flag=True, help="Clear existing ranks before seeding")
@click.option(
    "--new-members",
    is_flag=True,
    help="Create new voting members (default: use existing members without ranks)",
)
@click.option(
    "--category-participation",
    default=0.75,
    type=float,
    help="Probability of voting in each category (0.0-1.0, default: 0.75)",
)
@click.option(
    "--finalist-participation",
    default=0.85,
    type=float,
    help="Probability of ranking each finalist (0.0-1.0, default: 0.85)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be created without actually creating it",
)
def main(
    election_slug: str,
    count: int,
    clear: bool,
    new_members: bool,
    category_participation: float,
    finalist_participation: float,
    dry_run: bool,
):
    """Create voting ballots (ranks) for finalists in an election.

    This command simulates the final voting phase where members rank the finalists
    in each category. It can either create new voting members or use existing members
    who haven't voted yet.

    Args:
        election_slug: The slug of the election to process
        count: Number of voting members to create ballots for
        clear: If True, delete existing ranks before seeding
        new_members: If True, create new members; otherwise use existing members
        category_participation: Probability of voting in each category (0.0-1.0)
        finalist_participation: Probability of ranking each finalist (0.0-1.0)
    """
    console = Console()

    with suppress_sql_logging():
        try:
            election = Election.objects.get(slug=election_slug)
        except Election.DoesNotExist:
            console.print(f"[red]❌ Election '{election_slug}' not found[/red]")
            return

        console.print(
            f"[green]🗳️  Creating voting ballots for election: {election.name}[/green]"
        )
        console.print(f"[cyan]   Voters: {count}[/cyan]")
        console.print(
            f"[cyan]   Category participation: {category_participation * 100:.0f}%[/cyan]"
        )
        console.print(
            f"[cyan]   Finalist ranking rate: {finalist_participation * 100:.0f}%[/cyan]"
        )

        # Check if there are finalists
        categories = election.category_set.all()
        total_finalists = Finalist.objects.filter(category__election=election).count()
        if total_finalists == 0:
            console.print(
                "[red]❌ No finalists found in election. Run seed_finalists first![/red]"
            )
            return

        console.print(
            f"[cyan]   Found {total_finalists} finalists across {categories.count()} categories[/cyan]"
        )

        if dry_run:
            console.print("\n[yellow]DRY RUN MODE - No changes will be made[/yellow]")
            console.print(
                f"\nWould create ballots for {count} {'new ' if new_members else ''}members"
            )
            console.print(
                f"Category participation: {category_participation * 100:.0f}%"
            )
            console.print(f"Finalist ranking rate: {finalist_participation * 100:.0f}%")
            # Rough estimate
            avg_cats = categories.count() * category_participation
            avg_finalists = 6 * finalist_participation  # assuming ~6 finalists per cat
            estimated_ranks = int(count * avg_cats * avg_finalists)
            console.print(f"\nEstimated ranks: ~{estimated_ranks}")
            return

        if clear:
            with transaction.atomic():
                deleted = Rank.objects.filter(
                    finalist__category__election=election
                ).delete()[0]
                if deleted > 0:
                    console.print(
                        f"[yellow]   Cleared {deleted} existing ranks[/yellow]"
                    )

        # Get or create voting members
        members = []
        if new_members:
            console.print()
            console.print("[green]📝 Creating new voting members...[/green]")
            with transaction.atomic():
                # Get the highest existing member number to avoid duplicates
                existing_profiles = NominatingMemberProfile.objects.filter(
                    member_number__startswith="V-"
                ).order_by("-member_number")

                if existing_profiles.exists():
                    first_profile = existing_profiles.first()
                    # Type assertion for LSP - we know first() returns a profile when exists() is True
                    assert first_profile is not None
                    last_number = int(first_profile.member_number.split("-")[1])
                else:
                    last_number = 0

                for i in range(count):
                    member = create_voting_member(last_number + i + 1, election)
                    members.append(member)

            console.print(f"[green]   ✓ Created {len(members)} voting members[/green]")
        else:
            # Use existing members without ranks for this election
            console.print()
            console.print("[green]📝 Finding existing members without ranks...[/green]")

            # Find members who haven't voted in this election
            members_with_ranks = (
                Rank.objects.filter(finalist__category__election=election)
                .values_list("membership_id", flat=True)
                .distinct()
            )

            members = list(
                NominatingMemberProfile.objects.exclude(id__in=members_with_ranks)[
                    :count
                ]
            )

            if len(members) < count:
                console.print(
                    f"[yellow]   ⚠️  Only found {len(members)} members without ranks (requested {count})[/yellow]"
                )
                console.print(
                    "[cyan]   💡 Use --new-members flag to create new voting members[/cyan]"
                )
                if len(members) == 0:
                    console.print("[red]   ❌ No members available. Exiting.[/red]")
                    return
            else:
                console.print(
                    f"[green]   ✓ Found {len(members)} members without ranks[/green]"
                )

        # Create ballots
        console.print()
        console.print("[green]🗳️  Creating voting ballots...[/green]")

        total_categories_voted = 0
        total_ranks_created = 0

        with transaction.atomic():
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "[cyan]Creating ballots...", total=len(members)
                )

                for member in members:
                    categories_voted, ranks_created = create_ballot(
                        election,
                        member,
                        category_participation,
                        finalist_participation,
                    )

                    total_categories_voted += categories_voted
                    total_ranks_created += ranks_created

                    progress.update(task, advance=1)

        # Summary
        avg_categories = total_categories_voted / len(members) if members else 0
        avg_ranks = total_ranks_created / len(members) if members else 0

        console.print()
        console.print("[green bold]📊 Summary:[/green bold]")
        console.print(f"[cyan]   Total voting members: {len(members)}[/cyan]")
        console.print(f"[cyan]   Total ranks created: {total_ranks_created}[/cyan]")
        console.print(
            f"[cyan]   Average categories voted per member: {avg_categories:.1f}[/cyan]"
        )
        console.print(f"[cyan]   Average ranks per member: {avg_ranks:.1f}[/cyan]")

        console.print()
        console.print("[green bold]✅ Voting ballots seeding complete![/green bold]")

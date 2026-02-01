"""Management command to create finalists from existing nominations.

This command analyzes the nominations in an election and promotes the most-nominated
works to finalist status (the final ballot). It groups nominations by their field values,
counts them, and creates Finalist objects for the top N works in each category.

Usage:
    python manage.py seed_finalists <election_slug> [--count N] [--clear]

Example:
    python manage.py seed_finalists worldcon-2025 --count 6 --clear
"""

import djclick as click
from django.db import transaction
from django.db.models import Count
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)

from nomnom.convention_admin.management.commands._seed_base import suppress_sql_logging
from nomnom.nominate.models import Category, Election, Finalist, Nomination


def format_finalist_name(
    category: Category, field_1: str, field_2: str, field_3: str
) -> str:
    """Format a finalist name from nomination fields.

    Combines the fields according to the category's field configuration.
    For example:
    - 1 field: "Title"
    - 2 fields: "Title, Author"
    - 3 fields: "Title, Author (Publisher)"
    """
    fields = [field_1, field_2, field_3][: category.fields]
    # Filter out empty strings
    fields = [f.strip() for f in fields if f and f.strip()]

    if category.fields == 1:
        return fields[0] if fields else ""
    elif category.fields == 2:
        return ", ".join(fields)
    else:  # 3 fields
        if len(fields) >= 3:
            return f"{fields[0]}, {fields[1]} ({fields[2]})"
        else:
            return ", ".join(fields)


@click.command()
@click.argument("election_slug")
@click.option(
    "--count", default=6, help="Number of finalists per category (default: 6)"
)
@click.option("--clear", is_flag=True, help="Clear existing finalists before seeding")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be created without actually creating it",
)
def main(election_slug: str, count: int, clear: bool, dry_run: bool):
    """Create finalists from the most-nominated works in each category.

    This command counts nominations by work (grouped by field values), selects the
    top N works with the most nominations, and creates Finalist objects for them.
    It also adds "No Award" as the final ballot position.

    Args:
        election_slug: The slug of the election to process
        count: Number of finalists to create per category (default: 6)
        clear: If True, delete existing finalists before seeding
    """
    console = Console()

    with suppress_sql_logging():
        try:
            election = Election.objects.get(slug=election_slug)
        except Election.DoesNotExist:
            console.print(f"[red]❌ Election '{election_slug}' not found[/red]")
            return

        console.print(
            f"[green]🏆 Creating finalists for election: {election.name}[/green]"
        )
        console.print(f"[cyan]   Finalists per category: {count}[/cyan]")

        if dry_run:
            console.print("\n[yellow]DRY RUN MODE - No changes will be made[/yellow]")
            categories = list(election.category_set.all())
            console.print(f"\nWould create finalists for {len(categories)} categories")
            console.print(f"Finalists per category: {count} + 1 (No Award)")
            total = (count + 1) * len(categories)
            console.print(f"Total finalists: {total}")
            return

        if clear:
            with transaction.atomic():
                total_deleted = 0
                for category in election.category_set.all():
                    deleted = category.finalist_set.all().delete()[0]
                    total_deleted += deleted
                if total_deleted > 0:
                    console.print(
                        f"[yellow]   Cleared {total_deleted} existing finalists[/yellow]"
                    )

        categories = list(election.category_set.all())
        total_finalists = 0
        categories_with_finalists = 0
        categories_with_insufficient_data = 0

        with transaction.atomic():
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "[cyan]Creating finalists...", total=len(categories)
                )

                for category in categories:
                    # Count nominations grouped by field values
                    if category.fields == 1:
                        nomination_counts = (
                            Nomination.objects.filter(category=category)
                            .values("field_1")
                            .annotate(count=Count("id"))
                            .order_by("-count")[:count]
                        )
                    elif category.fields == 2:
                        nomination_counts = (
                            Nomination.objects.filter(category=category)
                            .values("field_1", "field_2")
                            .annotate(count=Count("id"))
                            .order_by("-count")[:count]
                        )
                    else:  # 3 fields
                        nomination_counts = (
                            Nomination.objects.filter(category=category)
                            .values("field_1", "field_2", "field_3")
                            .annotate(count=Count("id"))
                            .order_by("-count")[:count]
                        )

                    if not nomination_counts:
                        progress.console.print(
                            f"[yellow]   ⚠️  {category.name}: No nominations found, skipping[/yellow]"
                        )
                        categories_with_insufficient_data += 1
                        progress.update(task, advance=1)
                        continue

                    # Check if we have enough unique works
                    unique_works = len(nomination_counts)
                    if unique_works < 3:
                        progress.console.print(
                            f"[yellow]   ⚠️  {category.name}: Only {unique_works} unique works nominated, "
                            f"creating finalists anyway[/yellow]"
                        )
                        categories_with_insufficient_data += 1

                    # Create finalists for top N works
                    created_count = 0
                    for i, work_data in enumerate(nomination_counts):
                        field_1 = work_data.get("field_1", "")
                        field_2 = work_data.get("field_2", "")
                        field_3 = work_data.get("field_3", "")

                        name = format_finalist_name(category, field_1, field_2, field_3)

                        Finalist.objects.create(
                            category=category,
                            name=name,
                            ballot_position=i + 1,
                        )
                        created_count += 1

                    # Add "No Award" as the final position
                    Finalist.objects.create(
                        category=category,
                        name="No Award",
                        ballot_position=created_count + 1,
                    )
                    created_count += 1

                    total_finalists += created_count
                    categories_with_finalists += 1

                    # Show top 3 finalists for this category
                    top_3 = list(nomination_counts[:3])
                    top_3_str = ", ".join(
                        [
                            f"{format_finalist_name(category, w.get('field_1', ''), w.get('field_2', ''), w.get('field_3', ''))} ({w['count']})"
                            for w in top_3
                        ]
                    )
                    progress.console.print(
                        f"[green]   ✓ {category.name}: {created_count} finalists created[/green]"
                    )
                    progress.console.print(f"[cyan]      Top 3: {top_3_str}[/cyan]")

                    progress.update(task, advance=1)

        # Summary
        console.print()
        console.print("[green bold]📊 Summary:[/green bold]")
        console.print(f"[cyan]   Total finalists created: {total_finalists}[/cyan]")
        console.print(
            f"[cyan]   Categories with finalists: {categories_with_finalists}/{len(categories)}[/cyan]"
        )
        if categories_with_insufficient_data > 0:
            console.print(
                f"[yellow]   Categories with warnings: {categories_with_insufficient_data}[/yellow]"
            )

        console.print()
        console.print("[green bold]✅ Finalists seeding complete![/green bold]")

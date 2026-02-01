"""Create canonicalized Works by grouping similar nominations.

This command groups nominations with identical field values (case-insensitive) into Works.
It's useful for test data where variations like "Starlight Covenant" and "The Starlight Covenant"
should be grouped together.

The command uses the existing group_nominations() function from nomnom.canonicalize.models.
"""

import djclick as click
from django.db import transaction
from django.db.models import Count, F, Value
from django.db.models.functions import Concat, Lower
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)

from nomnom.canonicalize.models import Work, group_nominations
from nomnom.convention_admin.management.commands._seed_base import suppress_sql_logging
from nomnom.nominate.models import Election, Nomination


@click.command()
@click.argument("election_slug")
@click.option(
    "--categories",
    multiple=True,
    help="Specific category names to canonicalize (default: all categories)",
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear existing canonicalizations before seeding",
)
@click.option(
    "--min-nominations",
    type=int,
    default=2,
    help="Minimum nominations required to create a Work (default: 2)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be created without actually creating it",
)
def command(election_slug, categories, clear, min_nominations, dry_run):
    """Create canonicalized Works by grouping nominations with identical field values.

    Groups nominations that have the same field_1, field_2, field_3 values (case-insensitive)
    into Work objects. This is useful for test data where small variations should be grouped.

    Example:
        python manage.py seed_canonicalizations test-election --clear
        python manage.py seed_canonicalizations test-election --categories "Best Novel" --min-nominations 3
    """
    console = Console()

    with suppress_sql_logging():
        try:
            election = Election.objects.get(slug=election_slug)
        except Election.DoesNotExist:
            console.print(f"[red]Election '{election_slug}' not found[/red]")
            return

        # Clear existing canonicalizations if requested
        if clear:
            with transaction.atomic():
                work_count = Work.objects.filter(category__election=election).count()
                Work.objects.filter(category__election=election).delete()
                console.print(f"[yellow]Cleared {work_count} existing works[/yellow]")

        # Get categories to process
        category_qs = election.category_set.all()
        if categories:
            category_qs = category_qs.filter(name__in=categories)

        categories_list = list(category_qs)
        total_works_created = 0
        total_nominations_grouped = 0

        if dry_run:
            console.print("\n[yellow]DRY RUN MODE - No changes will be made[/yellow]")
            console.print(f"\nWould process {len(categories_list)} categories")
            console.print(f"Minimum nominations per work: {min_nominations}")
            # Count total uncanonicalized nominations
            total_noms = Nomination.objects.filter(
                category__in=categories_list, works__isnull=True
            ).count()
            console.print(f"Total uncanonicalized nominations: {total_noms}")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[cyan]Processing categories...", total=len(categories_list)
            )

            for category in categories_list:
                # Get all nominations for this category that aren't already canonicalized
                nominations = Nomination.objects.filter(
                    category=category, works__isnull=True
                ).select_related("category")

                if not nominations.exists():
                    progress.console.print(
                        f"[yellow]  {category.name}: No uncanonicalized nominations[/yellow]"
                    )
                    progress.update(task, advance=1)
                    continue

                # Group nominations by their combined field values (case-insensitive)
                works_created = 0
                nominations_grouped = 0

                # Build the annotation based on field count
                field_count = category.fields
                if field_count == 1:
                    combined_field = Lower(F("field_1"))
                elif field_count == 2:
                    combined_field = Lower(
                        Concat("field_1", Value(" "), "field_2", output_field=None)
                    )
                elif field_count == 3:
                    combined_field = Lower(
                        Concat(
                            "field_1",
                            Value(" "),
                            "field_2",
                            Value(" "),
                            "field_3",
                            output_field=None,
                        )
                    )
                else:
                    progress.console.print(
                        f"[yellow]  {category.name}: Skipping: unsupported field count {field_count}[/yellow]"
                    )
                    progress.update(task, advance=1)
                    continue

                # Group by the combined field and count
                grouped = (
                    nominations.annotate(combined=combined_field)
                    .values("combined")
                    .annotate(count=Count("id"))
                    .filter(count__gte=min_nominations)
                    .order_by("-count")
                )

                if not grouped:
                    progress.console.print(
                        f"[yellow]  {category.name}: No groups with >={min_nominations} nominations found[/yellow]"
                    )
                    progress.update(task, advance=1)
                    continue

                # Create Works for each group
                with transaction.atomic():
                    for group in grouped:
                        combined_value = group["combined"]
                        nomination_count = group["count"]

                        # Get nominations for this group by re-filtering
                        group_noms = nominations.annotate(
                            combined=combined_field
                        ).filter(combined=combined_value)

                        if not group_noms.exists():
                            continue

                        # Use group_nominations() to create the Work
                        try:
                            group_nominations(group_noms, work=None)
                            works_created += 1
                            nominations_grouped += nomination_count
                        except Exception:
                            continue

                progress.console.print(
                    f"[green]  {category.name}: Created {works_created} works from {nominations_grouped} nominations[/green]"
                )
                total_works_created += works_created
                total_nominations_grouped += nominations_grouped

                progress.update(task, advance=1)

        console.print()
        console.print("[cyan bold]Summary:[/cyan bold]")
        color = "green" if total_works_created > 0 else "yellow"
        console.print(
            f"[{color}]  Total works created: {total_works_created}[/{color}]"
        )
        console.print(
            f"[{color}]  Total nominations grouped: {total_nominations_grouped}[/{color}]"
        )

        if total_works_created == 0:
            console.print()
            console.print(
                "[yellow bold]No works were created. This might be because:[/yellow bold]"
            )
            console.print(
                "[yellow]  - All nominations are already canonicalized (try --clear)[/yellow]"
            )
            console.print(
                f"[yellow]  - No groups have >={min_nominations} nominations (try --min-nominations 1)[/yellow]"
            )

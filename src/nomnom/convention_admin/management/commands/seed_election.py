"""
Management command to seed an election with Hugo Awards categories.

Usage:
    python manage.py seed_election <slug> <name> [--year YEAR] [--categories-file FILE]

Examples:
    python manage.py seed_election 2025-hugos "2025 Hugo Awards"
    python manage.py seed_election 2025-hugos "2025 Hugo Awards" --year 2025
    python manage.py seed_election the-hugo-awards "The Hugo Awards" --categories-file path/to/custom.json
"""

import json
from pathlib import Path

import djclick as click
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
from nomnom.convention_admin.seed_data.hugo_categories import HUGO_CATEGORIES
from nomnom.nominate.models import Category, Election


@click.command()
@click.argument("slug")
@click.argument("name")
@click.option(
    "--year",
    type=int,
    default=2025,
    help="Year for the Hugo Awards (default: 2025)",
)
@click.option(
    "--categories-file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to custom categories JSON file (overrides built-in categories)",
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear existing categories for this election before seeding",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be created without actually creating it",
)
def main(
    slug: str,
    name: str,
    year: int,
    categories_file: Path | None,
    clear: bool,
    dry_run: bool,
):
    """
    Seed an election with Hugo Awards categories.

    Creates an Election object and populates it with official Hugo Award
    categories, including proper field definitions.

    By default, uses the built-in 2025 Hugo Awards categories from
    nomnom.admin.seed_data.hugo_categories. You can override this with
    a custom JSON file using --categories-file.

    Args:
        slug: URL-friendly identifier for the election (e.g., "2025-hugos")
        name: Display name for the election (e.g., "2025 Hugo Awards")
        year: Year for the awards (default: 2025)
        categories_file: Optional custom categories JSON file
        clear: If True, delete existing categories for this election first
    """
    console = Console()

    with suppress_sql_logging():
        # Load categories data
        if categories_file:
            # Load from custom JSON file
            if not categories_file.exists():
                console.print(
                    f"[red]Error: Categories file not found: {categories_file}[/red]"
                )
                raise click.Abort()

            try:
                with categories_file.open() as f:
                    data = json.load(f)
                    categories_data = data.get("categories", [])
            except json.JSONDecodeError as e:
                console.print(f"[red]Error: Invalid JSON in categories file: {e}[/red]")
                raise click.Abort()
            except Exception as e:
                console.print(f"[red]Error loading categories file: {e}[/red]")
                raise click.Abort()

            if not categories_data:
                console.print("[red]Error: No categories found in file[/red]")
                raise click.Abort()

            console.print(
                f"[cyan]Loaded {len(categories_data)} categories from: {categories_file}[/cyan]"
            )
        else:
            # Use built-in Hugo categories
            categories_data = HUGO_CATEGORIES
            console.print(
                f"[cyan]Using built-in Hugo categories ({len(categories_data)} categories)[/cyan]"
            )

        if not categories_data:
            console.print("[red]Error: No categories found in file[/red]")
            raise click.Abort()

        if dry_run:
            console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")
            console.print(f"\nWould create election: {name} (slug: {slug})")
            console.print(f"Categories to create: {len(categories_data)}")
            for i, cat in enumerate(categories_data[:3], 1):
                console.print(f"  {i}. {cat['name']}")
            if len(categories_data) > 3:
                console.print(f"  ... and {len(categories_data) - 3} more")
            return

        # Create or get election
        with transaction.atomic():
            election, created = Election.objects.get_or_create(
                slug=slug,
                defaults={"name": name},
            )

            if not created:
                console.print(
                    f"[yellow]Election '{election.name}' already exists (slug: {slug})[/yellow]"
                )

                if clear:
                    # Delete existing categories
                    existing_count = election.category_set.count()
                    if existing_count > 0:
                        election.category_set.all().delete()
                        console.print(
                            f"[yellow]Cleared {existing_count} existing categories[/yellow]"
                        )
            else:
                console.print(
                    f"[green]Created election: {election.name} (slug: {slug})[/green]"
                )

            # Create categories
            categories_created = 0
            categories_skipped = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "[cyan]Creating categories...", total=len(categories_data)
                )

                for cat_data in categories_data:
                    # Check if category already exists
                    existing = Category.objects.filter(
                        election=election,
                        ballot_position=cat_data["ballot_position"],
                    ).first()

                    if existing and not clear:
                        categories_skipped += 1
                        progress.update(task, advance=1)
                        continue

                    # Create category
                    Category.objects.create(
                        election=election,
                        name=cat_data["name"],
                        description=cat_data.get("description", ""),
                        nominating_details=cat_data.get("nominating_details", ""),
                        ballot_position=cat_data["ballot_position"],
                        fields=cat_data["fields"],
                        field_1_description=cat_data["field_1_description"],
                        field_2_description=cat_data.get("field_2_description", ""),
                        field_2_required=cat_data.get("field_2_required", True),
                        field_3_description=cat_data.get("field_3_description", ""),
                        field_3_required=cat_data.get("field_3_required", True),
                    )

                    categories_created += 1
                    progress.update(task, advance=1)

        # Summary
        console.print()
        console.print("[bold]Summary:[/bold]")
        console.print(f"  Election: {election.name} (slug: {slug})")
        console.print(f"  Categories created: {categories_created}")
        if categories_skipped > 0:
            console.print(f"  Categories skipped: {categories_skipped}")
        console.print(f"  Total categories: {election.category_set.count()}")
        console.print()
        console.print(
            "[green bold]✓ Election seeded successfully! You can now run seed_members or seed_nominations.[/green bold]"
        )

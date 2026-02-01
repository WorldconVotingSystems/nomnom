"""
Master command to orchestrate complete seeding workflow.

This command runs all seeding commands in the correct order to create a
complete test dataset for an election.
"""

from django.core.management import call_command
from django.db import transaction
from django.core.management.base import BaseCommand
from rich.console import Console


class Command(BaseCommand):
    help = "Orchestrate complete seeding workflow for an election"

    def add_arguments(self, parser):
        parser.add_argument("election_slug", type=str, help="Election slug")
        parser.add_argument(
            "election_name",
            type=str,
            nargs="?",
            default=None,
            help="Election name (optional, derived from slug if not provided)",
        )
        parser.add_argument(
            "--quick",
            action="store_true",
            help="Quick mode: Small dataset (20 nominators, 30 voters)",
        )
        parser.add_argument(
            "--full",
            action="store_true",
            help="Full mode: Large dataset (200 nominators, 300 voters)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing data for this election before seeding",
        )
        parser.add_argument(
            "--skip-election",
            action="store_true",
            help="Skip creating election and categories (assumes it exists)",
        )
        parser.add_argument(
            "--skip-packet",
            action="store_true",
            help="Skip creating Hugo packet structure",
        )
        parser.add_argument(
            "--finalists",
            type=int,
            default=6,
            help="Number of finalists per category (default: 6)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating it",
        )

    @transaction.atomic()
    def handle(self, *args, **options):
        console = Console()

        election_slug = options["election_slug"]
        election_name = options["election_name"]
        quick = options["quick"]
        full = options["full"]
        clear = options["clear"]
        skip_election = options["skip_election"]
        skip_packet = options["skip_packet"]
        finalist_count = options["finalists"]
        dry_run = options["dry_run"]

        # Validate modes
        if quick and full:
            console.print("[red]❌ Cannot use both --quick and --full[/red]")
            return

        # Determine dataset size
        if quick:
            nominators = 20
            voters = 30
            mode_name = "Quick"
        elif full:
            nominators = 200
            voters = 300
            mode_name = "Full"
        else:
            nominators = 50
            voters = 100
            mode_name = "Standard"

        # Derive election name from slug if not provided
        if not election_name and not skip_election:
            election_name = election_slug.replace("-", " ").title()

        if dry_run:
            console.print(
                "\n[yellow bold]DRY RUN MODE - No changes will be made[/yellow bold]\n"
            )

        console.print()
        console.print(
            f"[cyan bold]🚀 Starting {mode_name} Seeding Workflow[/cyan bold]"
        )
        console.print(f"[cyan]   Election: {election_slug}[/cyan]")
        console.print(f"[cyan]   Nominators: {nominators}[/cyan]")
        console.print(f"[cyan]   Voters: {voters}[/cyan]")
        console.print(f"[cyan]   Finalists per category: {finalist_count}[/cyan]")

        if dry_run:
            console.print("\n[yellow]Workflow steps:[/yellow]")
            if not skip_election:
                console.print("[yellow]  1. Create election and categories[/yellow]")
            else:
                console.print(
                    "[yellow]  1. [Skipped] Create election and categories[/yellow]"
                )
            console.print(
                f"[yellow]  2. Create {nominators} members with nominations[/yellow]"
            )
            console.print("[yellow]  3. Group nominations into works[/yellow]")
            console.print(
                f"[yellow]  4. Select top {finalist_count} finalists per category[/yellow]"
            )
            console.print(f"[yellow]  5. Create {voters} voting ballots[/yellow]")
            if not skip_packet:
                console.print("[yellow]  6. Create Hugo packet structure[/yellow]")
            else:
                console.print(
                    "[yellow]  6. [Skipped] Create Hugo packet structure[/yellow]"
                )
            console.print()
            return

        try:
            # Step 1: Create election and categories
            if not skip_election:
                console.print()
                console.print(
                    "[green]📋 Step 1/6: Creating election and categories...[/green]"
                )
                call_command(
                    "seed_election",
                    election_slug,
                    election_name,
                    clear=clear,
                )
            else:
                console.print()
                console.print("[yellow]📋 Step 1/6: Skipped (--skip-election)[/yellow]")

            # Step 2: Create nominations
            console.print()
            console.print("[green]📝 Step 2/6: Creating nominations...[/green]")
            call_command(
                "seed_nominations",
                election_slug,
                count=nominators,
                clear=clear,
            )

            # Step 3: Create canonicalizations (group nominations into works)
            console.print()
            console.print(
                "[green]🔗 Step 3/6: Grouping nominations into works...[/green]"
            )
            call_command(
                "seed_canonicalizations",
                election_slug,
                clear=clear,
                min_nominations=2,
            )

            # Step 4: Create finalists
            console.print()
            console.print("[green]⭐ Step 4/6: Selecting finalists...[/green]")
            call_command(
                "seed_finalists",
                election_slug,
                count=finalist_count,
                clear=clear,
            )

            # Step 5: Create voting ranks
            console.print()
            console.print("[green]🗳️  Step 5/6: Creating voting ballots...[/green]")
            call_command(
                "seed_ranks",
                election_slug,
                count=voters,
                new_members=True,
                clear=clear,
            )

            # Step 6: Create Hugo packet (optional)
            if not skip_packet:
                console.print()
                console.print(
                    "[green]📦 Step 6/6: Creating Hugo packet structure...[/green]"
                )
                try:
                    call_command(
                        "seed_packet",
                        election_slug,
                        bucket="test-bucket",
                        fake_s3=True,
                    )
                except Exception as e:
                    console.print(
                        f"[yellow]⚠️  Warning: Packet creation failed: {e}[/yellow]"
                    )
                    console.print(
                        "[yellow]   (This is expected if nomnom.hugopacket is not configured)[/yellow]"
                    )
            else:
                console.print()
                console.print("[yellow]📦 Step 6/6: Skipped (--skip-packet)[/yellow]")

            # Success summary
            console.print()
            console.print("[green]" + "=" * 60 + "[/green]")
            console.print("[green bold]✅ Seeding Workflow Complete![/green bold]")
            console.print("[green]" + "=" * 60 + "[/green]")
            console.print()
            console.print(
                f"[green]Election '{election_slug}' is ready for testing![/green]"
            )
            console.print()
            console.print("[cyan]You can now:[/cyan]")
            console.print(
                "[cyan]  • View nominations: /admin/nominate/nomination/[/cyan]"
            )
            console.print("[cyan]  • View finalists: /admin/nominate/finalist/[/cyan]")
            console.print("[cyan]  • View votes: /admin/nominate/rank/[/cyan]")
            console.print("[cyan]  • Start dev server: just dev-serve[/cyan]")

        except Exception as e:
            console.print()
            console.print(f"[red bold]❌ Seeding workflow failed: {e}[/red bold]")
            console.print()
            console.print("[yellow]Partial data may have been created.[/yellow]")
            console.print("[yellow]Use --clear flag to reset and try again.[/yellow]")
            raise

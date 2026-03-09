"""Management command to create Hugo packet structure with files and distribution codes.

This command generates a comprehensive, realistic Hugo packet structure for testing purposes.
It creates packet files, sections, and distribution codes based on existing finalists in an election.

Usage:
    python manage.py seed_packet <election_slug> [--bucket NAME] [--fake-s3] [--clear]

Example:
    python manage.py seed_packet test-2025 --bucket test-bucket --fake-s3 --clear
"""

import random
import string
from collections import defaultdict

import djclick as click
from django.db import transaction
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from nomnom.convention_admin.management.commands._seed_base import suppress_sql_logging
from nomnom.hugopacket.models import (
    DistributionCode,
    ElectionPacket,
    PacketFile,
    PacketSection,
)
from nomnom.nominate.models import Election, Finalist

# Organizational strategies for packet structure
STRATEGY_FULL = "full"  # One download for entire category
STRATEGY_INDIVIDUAL = "individual"  # One download per finalist
STRATEGY_BOTH = "both"  # Both full category + individual downloads
STRATEGY_CODES = "codes"  # Distribution codes (for games)

# Game category identification
GAME_CATEGORY_BALLOT_POSITION = 10


def generate_code(length: int = 12) -> str:
    """Generate a random alphanumeric code without hyphens."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def get_file_extension(strategy: str, is_full: bool = False) -> str:
    """Determine file extension based on strategy and type."""
    if is_full or strategy == STRATEGY_FULL:
        return "zip"
    # Individual files - mix of formats
    return random.choice(["pdf", "epub", "mobi", "pdf"])


def get_file_size_mb(strategy: str, is_full: bool = False) -> int:
    """Generate realistic file size in MB."""
    if is_full or strategy == STRATEGY_FULL:
        return random.randint(50, 500)  # Large bundles
    return random.randint(1, 50)  # Individual works


def create_packet_file(
    packet: ElectionPacket,
    section: PacketSection,
    name: str,
    s3_key: str,
    position: int,
    access_type: str = PacketFile.AccessType.DOWNLOAD,
) -> PacketFile:
    """Create a packet file with given parameters."""
    return PacketFile.objects.create(
        packet=packet,
        section=section,
        name=name,
        s3_object_key=s3_key,
        position=position,
        access_type=access_type,
        available=True,
    )


def create_distribution_codes(
    packet_file: PacketFile, count: int, console: Console
) -> None:
    """Create distribution codes for a packet file."""
    codes = []
    for _ in range(count):
        code = generate_code()
        codes.append(
            DistributionCode(
                packet_file=packet_file,
                code=code,
            )
        )
    DistributionCode.objects.bulk_create(codes)
    console.print(f"         Created {count} distribution codes")


@click.command()
@click.argument("election_slug")
@click.option("--bucket", default="test-bucket", help="S3 bucket name for files")
@click.option(
    "--fake-s3",
    is_flag=True,
    help="Use fake S3 (for testing without real S3 access)",
)
@click.option("--clear", is_flag=True, help="Clear existing packet before seeding")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be created without actually creating it",
)
def main(
    election_slug: str, bucket: str, fake_s3: bool, clear: bool, dry_run: bool
) -> None:
    """Create a comprehensive Hugo packet structure for testing.

    This command generates:
    - Packet sections organized by category
    - Mix of organizational strategies (full/individual/both/codes)
    - Distribution codes for game category
    - Whole-packet download at root level

    Args:
        election_slug: The slug of the election to process
        bucket: S3 bucket name for storing files
        fake_s3: If True, use fake S3 for testing
        clear: If True, delete existing packet before seeding
        dry_run: If True, show what would be created without creating it
    """
    console = Console()

    with suppress_sql_logging():
        try:
            election = Election.objects.get(slug=election_slug)
        except Election.DoesNotExist:
            console.print(f"[red]❌ Election '{election_slug}' not found[/red]")
            return

        console.print(
            f"[green]📦 Creating Hugo packet for election: {election.name}[/green]"
        )
        console.print(f"[cyan]   S3 Bucket: {bucket}[/cyan]")
        console.print(f"[cyan]   Fake S3: {fake_s3}[/cyan]")

        # Get finalists grouped by category
        finalists_by_category = defaultdict(list)
        for finalist in (
            Finalist.objects.filter(category__election=election)
            .select_related("category")
            .order_by("category__ballot_position", "ballot_position")
        ):
            finalists_by_category[finalist.category].append(finalist)

        categories_with_finalists = len(finalists_by_category)

        if categories_with_finalists == 0:
            console.print(
                "[yellow]⚠️  No finalists found. Run seed_finalists first.[/yellow]"
            )
            return

        console.print(
            f"[cyan]   Categories with finalists: {categories_with_finalists}[/cyan]"
        )

        if dry_run:
            console.print("\n[yellow]DRY RUN MODE - No changes will be made[/yellow]")
            console.print(
                f"\nWould create packet structure for {categories_with_finalists} categories"
            )
            console.print("Would include:")
            console.print("  - Category sections with mixed strategies")
            console.print("  - Distribution codes for game category")
            console.print("  - Whole packet download section")
            return

        # Check for existing packet
        try:
            existing_packet = ElectionPacket.objects.get(election=election)
            if clear:
                with transaction.atomic():
                    # Cascade will delete sections, files, codes, etc.
                    existing_packet.delete()
                    console.print("[yellow]   Cleared existing packet[/yellow]")
            else:
                console.print(
                    "[red]❌ Packet already exists. Use --clear to replace it.[/red]"
                )
                return
        except ElectionPacket.DoesNotExist:
            pass

        year = election.slug.split("-")[-1]  # Extract year from slug

        with transaction.atomic():
            # Create election packet
            packet = ElectionPacket.objects.create(
                election=election,
                name=f"{election.name} Hugo Packet",
                s3_bucket_name=bucket,
                enabled=True,
            )

            stats = {
                "sections": 0,
                "files": 0,
                "codes": 0,
                "strategies": defaultdict(int),
            }

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "[cyan]Creating packet structure...",
                    total=categories_with_finalists + 1,
                )

                # Process each category
                for category, finalists in finalists_by_category.items():
                    # Determine organizational strategy
                    is_game_category = (
                        category.ballot_position == GAME_CATEGORY_BALLOT_POSITION
                    )

                    if is_game_category:
                        strategy = STRATEGY_CODES
                    else:
                        strategy = random.choice(
                            [STRATEGY_FULL, STRATEGY_INDIVIDUAL, STRATEGY_BOTH]
                        )

                    stats["strategies"][strategy] += 1

                    # Create top-level category section
                    category_section = PacketSection.objects.create(
                        packet=packet,
                        parent=None,
                        name=category.name,
                        description=f"Finalists for {category.name}",
                        position=category.ballot_position,
                    )
                    stats["sections"] += 1

                    progress.console.print(
                        f"[green]   ✓ {category.name} (strategy: {strategy})[/green]"
                    )

                    # Create files based on strategy
                    if strategy == STRATEGY_FULL:
                        # Single download for entire category
                        ext = get_file_extension(strategy, is_full=True)
                        s3_key = f"{year}/cat-{category.ballot_position}/complete.{ext}"
                        file = create_packet_file(
                            packet=packet,
                            section=category_section,
                            name=f"Complete {category.name} Packet",
                            s3_key=s3_key,
                            position=1,
                        )
                        stats["files"] += 1

                    elif strategy == STRATEGY_INDIVIDUAL:
                        # One download per finalist
                        for idx, finalist in enumerate(finalists, start=1):
                            if finalist.name == "No Award":
                                continue
                            ext = get_file_extension(strategy)
                            s3_key = f"{year}/cat-{category.ballot_position}/finalist-{finalist.ballot_position}.{ext}"
                            file = create_packet_file(
                                packet=packet,
                                section=category_section,
                                name=finalist.name,
                                s3_key=s3_key,
                                position=idx,
                            )
                            stats["files"] += 1

                    elif strategy == STRATEGY_BOTH:
                        # Full category download
                        ext = get_file_extension(strategy, is_full=True)
                        s3_key = f"{year}/cat-{category.ballot_position}/complete.{ext}"
                        file = create_packet_file(
                            packet=packet,
                            section=category_section,
                            name=f"Complete {category.name} Packet",
                            s3_key=s3_key,
                            position=1,
                        )
                        stats["files"] += 1

                        # Individual finalist downloads
                        for idx, finalist in enumerate(finalists, start=2):
                            if finalist.name == "No Award":
                                continue
                            ext = get_file_extension(strategy)
                            s3_key = f"{year}/cat-{category.ballot_position}/finalist-{finalist.ballot_position}.{ext}"
                            file = create_packet_file(
                                packet=packet,
                                section=category_section,
                                name=finalist.name,
                                s3_key=s3_key,
                                position=idx,
                            )
                            stats["files"] += 1

                    elif strategy == STRATEGY_CODES:
                        # Distribution codes for each game
                        game_with_no_codes = random.randint(
                            0, len(finalists) - 1
                        )  # One game gets no codes
                        for idx, finalist in enumerate(finalists):
                            if finalist.name == "No Award":
                                continue

                            s3_key = f"{year}/cat-{category.ballot_position}/game-{finalist.ballot_position}"
                            file = create_packet_file(
                                packet=packet,
                                section=category_section,
                                name=finalist.name,
                                s3_key=s3_key,
                                position=idx + 1,
                                access_type=PacketFile.AccessType.CODE,
                            )
                            stats["files"] += 1

                            # Create distribution codes (except for one game)
                            if idx != game_with_no_codes:
                                code_count = random.randint(5, 10)
                                create_distribution_codes(
                                    file, code_count, progress.console
                                )
                                stats["codes"] += code_count

                    progress.update(task, advance=1)

                # Create whole-packet download section at root level
                whole_packet_section = PacketSection.objects.create(
                    packet=packet,
                    parent=None,
                    name="Complete Hugo Packet",
                    description="Download the entire Hugo packet in one file",
                    position=0,  # Put it at the start
                )
                stats["sections"] += 1

                s3_key = f"{year}/hugo-packet-complete.zip"
                file = create_packet_file(
                    packet=packet,
                    section=whole_packet_section,
                    name="Complete Hugo Packet (All Categories)",
                    s3_key=s3_key,
                    position=1,
                )
                stats["files"] += 1

                progress.console.print(
                    "[green]   ✓ Complete Hugo Packet section created[/green]"
                )
                progress.update(task, advance=1)

        # Summary
        console.print()
        console.print("[green bold]📊 Summary:[/green bold]")
        console.print(f"[cyan]   Total sections: {stats['sections']}[/cyan]")
        console.print(f"[cyan]   Total files: {stats['files']}[/cyan]")
        console.print(f"[cyan]   Total distribution codes: {stats['codes']}[/cyan]")
        console.print("[cyan]   Strategies used:[/cyan]")
        for strategy, count in stats["strategies"].items():
            console.print(f"[cyan]     - {strategy}: {count} categories[/cyan]")

        console.print()
        console.print("[green bold]✅ Packet seeding complete![/green bold]")

from django.conf import settings
from django.db import models
from django.http import HttpRequest
from django.utils import timezone
from django_svcs.apps import svcs_from

from nomnom.hugopacket.apps import PacketAccess
from nomnom.nominate.models import NominatingMemberProfile


class ElectionPacket(models.Model):
    class Meta:
        permissions = [
            ("preview_packet", "Has early access to the packet"),
        ]

    election = models.OneToOneField(
        "nominate.Election", on_delete=models.SET_NULL, null=True
    )

    name = models.CharField(max_length=255)
    s3_bucket_name = models.CharField(max_length=255)
    enabled = models.BooleanField(
        default=False,
        help_text="When not enabled, this packet's page will show up as not found",
    )

    def available(self, nominator: NominatingMemberProfile) -> bool:
        return self.election.user_can_vote(nominator.user)

    def __str__(self) -> str:
        return self.name if self.name else f"The {self.election.name} Packet"


class PacketSection(models.Model):
    """Hierarchical organizational structure for packet contents."""

    class Meta:
        ordering = ["position"]

    packet = models.ForeignKey(
        ElectionPacket, on_delete=models.CASCADE, related_name="sections"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subsections",
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Supports markdown")
    position = models.PositiveSmallIntegerField()

    def __str__(self) -> str:
        return self.name

    @property
    def full_path(self) -> str:
        """Return hierarchical path like 'Best Novel / Author Name / Downloads'"""
        if self.parent:
            return f"{self.parent.full_path} / {self.name}"
        return self.name

    @property
    def depth(self) -> int:
        """How deep in the hierarchy (0 = top level)"""
        if self.parent:
            return self.parent.depth + 1
        return 0


class PacketFile(models.Model):
    """Packet file with access tracking."""

    class AccessType(models.TextChoices):
        DOWNLOAD = "download", "Download (S3 file)"
        CODE = "code", "Distribution Code"

    class Meta:
        ordering = ["position"]
        verbose_name = "Packet Item"
        verbose_name_plural = "Packet Items"

    packet = models.ForeignKey(ElectionPacket, on_delete=models.CASCADE)
    section = models.ForeignKey(
        PacketSection,
        on_delete=models.CASCADE,
        related_name="files",
        null=True,
        blank=True,
        help_text="Optional: organize files into hierarchical sections",
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Allows markdown")
    available = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=0)

    # Access configuration
    access_type = models.CharField(
        max_length=20,
        choices=AccessType.choices,
        default=AccessType.DOWNLOAD,
        help_text="How members access this content",
    )
    s3_object_key = models.CharField(
        max_length=65536, help_text="Used for DOWNLOAD type"
    )
    code_display_format = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional format template for CODE type display. Use '#' for each character. Example: '###-#####-###-####' formats 'ABC12345DEF6789' as 'ABC-12345-DEF-6789'. Leave blank for no formatting.",
    )

    def __str__(self) -> str:
        return self.name if self.name else self.s3_object_key.split("/")[-1]

    def format_code(self, code: str) -> str:
        """
        Format a code according to the display format template.
        Returns the formatted code for display, or the original if no format specified.
        """
        if not self.code_display_format:
            return code

        # Remove any non-alphanumeric characters from the code for formatting
        clean_code = "".join(c for c in code if c.isalnum())

        result = []
        code_idx = 0

        for char in self.code_display_format:
            if char == "#":
                if code_idx < len(clean_code):
                    result.append(clean_code[code_idx])
                    code_idx += 1
                else:
                    # No more code characters, break out of the loop
                    result.append(clean_code[code_idx:])
                    break
            else:
                # Only add separator if we haven't run out of code chars
                if code_idx < len(clean_code):
                    result.append(char)

        # the result may have leftover code characters if the format has fewer '#' than the code
        # length. Append any remaining characters at the end, because the whole code should be visible even if the format is shorter.
        result.append(clean_code[code_idx:])

        return "".join(result)

    def get_download_url(self, request: HttpRequest) -> str:
        """Legacy method for backward compatibility."""
        packet_access = svcs_from(request).get(PacketAccess)
        resolver = packet_access.resolver(
            bucket_name=self.packet.s3_bucket_name, file_key=self.s3_object_key
        )
        return resolver.get_url()


class PacketItemAccess(models.Model):
    """Tracks member access to packet files."""

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["packet_file", "member"],
                name="unique_access_per_member_per_file",
            )
        ]
        ordering = ["-last_accessed_at"]
        verbose_name = "Item Access"
        verbose_name_plural = "Item Accesses"

    packet_file = models.ForeignKey(
        PacketFile, on_delete=models.CASCADE, related_name="member_accesses"
    )
    member = models.ForeignKey(
        NominatingMemberProfile,
        on_delete=models.PROTECT,
        related_name="packet_accesses",
    )

    # Access tracking
    first_accessed_at = models.DateTimeField(auto_now_add=True)
    last_accessed_at = models.DateTimeField(auto_now=True)
    access_count = models.PositiveIntegerField(default=0)

    # For CODE type: link to assigned code
    distribution_code = models.OneToOneField(
        "DistributionCode",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_record",
    )

    def __str__(self) -> str:
        return f"{self.member.display_name} → {self.packet_file.name}"

    def get_access_url(self, request: HttpRequest) -> str:
        """Get appropriate access URL based on packet file type."""
        if self.packet_file.access_type == PacketFile.AccessType.DOWNLOAD:
            return self.get_download_url(request)

        # For CODE type, views should handle displaying the code
        raise ValueError(
            f"Cannot get URL for access type {self.packet_file.access_type}"
        )

    def get_download_url(self, request: HttpRequest) -> str:
        """Get pre-signed S3 URL for downloading the file."""

        packet_access = svcs_from(request).get(PacketAccess)
        resolver = packet_access.resolver(
            bucket_name=self.packet_file.packet.s3_bucket_name,
            file_key=self.packet_file.s3_object_key,
        )

        return resolver.get_url()

    def increment_access(self) -> None:
        """Record an access event."""
        self.access_count += 1
        self.last_accessed_at = timezone.now()
        self.save(update_fields=["access_count", "last_accessed_at"])


class DistributionCode(models.Model):
    """Pool of codes available for assignment to a packet file."""

    class Meta:
        ordering = ["packet_file", "assigned_at"]
        verbose_name = "Distribution Code"
        verbose_name_plural = "Distribution Codes"

    packet_file = models.ForeignKey(
        PacketFile, on_delete=models.CASCADE, related_name="code_pool"
    )
    code = models.CharField(max_length=500)

    # Assignment tracking
    assigned_at = models.DateTimeField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="codes_assigned",
        help_text="Admin who manually assigned this code",
    )

    notes = models.TextField(blank=True, help_text="Internal notes about this code")

    def __str__(self) -> str:
        access = getattr(self, "access_record", None)
        if access:
            return f"{self.code} → {access.member.display_name}"
        return f"{self.code} (unassigned)"

    @property
    def member(self) -> NominatingMemberProfile | None:
        """Convenience property to get assigned member through access_record."""
        access = getattr(self, "access_record", None)
        return access.member if access else None

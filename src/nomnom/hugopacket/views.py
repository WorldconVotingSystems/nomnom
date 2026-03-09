from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse

from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Prefetch
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.utils import timezone
from django_svcs.apps import svcs_from

from nomnom.hugopacket.apps import S3Client
from nomnom.hugopacket.models import (
    DistributionCode,
    ElectionPacket,
    PacketFile,
    PacketItemAccess,
)
from nomnom.nominate.models import Election


@dataclass
class PacketFileMetadata:
    last_modified: datetime
    size: int


@dataclass
class PacketFileDisplay:
    packet_file: PacketFile
    metadata: PacketFileMetadata | None

    @property
    def id(self):
        return self.packet_file.id

    @property
    def description(self):
        return self.packet_file.description

    def __str__(self):
        return self.packet_file.name


def request_passes_test(
    test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME
):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapper_view(request, *args, **kwargs):
            if test_func(request):
                return view_func(request, *args, **kwargs)
            path = request.build_absolute_uri()
            resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)
            # If the login url is the same scheme and net location then just
            # use the path as the "next" url.
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if (not login_scheme or login_scheme == current_scheme) and (
                not login_netloc or login_netloc == current_netloc
            ):
                path = request.get_full_path()
            from django.contrib.auth.views import redirect_to_login

            return redirect_to_login(path, resolved_login_url, redirect_field_name)

        return _wrapper_view

    return decorator


def member_can_vote():
    def test_func(request: HttpRequest) -> bool:
        election_id = request.resolver_match.kwargs.get("election_id")

        if not get_object_or_404(Election, slug=election_id).user_can_vote(
            request.user
        ):
            raise PermissionDenied()

        return True

    return request_passes_test(test_func)


@login_required
@member_can_vote()
def index(request: HttpRequest, election_id: str) -> HttpResponse:
    election = get_object_or_404(Election, slug=election_id)
    packet = get_object_or_404(ElectionPacket, election=election)

    # the packet is allowed for members with voting preview, even if inactive
    if not packet.enabled and not request.user.has_perm("hugopacket.preview_packet"):
        raise Http404()

    # Get member profile for access tracking
    member = request.user.convention_profile

    # Prefetch access records for the current member to avoid N+1 queries
    member_access_prefetch = Prefetch(
        "member_accesses",
        queryset=PacketItemAccess.objects.filter(member=member),
        to_attr="prefetched_member_access",
    )

    # Build hierarchical section structure
    root_sections = packet.sections.filter(parent__isnull=True).prefetch_related(
        "subsections",
        Prefetch(
            "files",
            queryset=PacketFile.objects.prefetch_related(member_access_prefetch),
        ),
    )

    # For backward compatibility: get files without sections
    orphan_files = packet.packetfile_set.filter(section__isnull=True).prefetch_related(
        member_access_prefetch
    )

    # Get all packet files with access records prefetched
    all_packet_files = packet.packetfile_set.all().prefetch_related(
        member_access_prefetch
    )

    # Get S3 metadata for all files
    all_prefixes = set()
    for packet_file in all_packet_files:
        all_prefixes.add(packet_file.s3_object_key.rsplit("/", 1)[0])

    s3 = svcs_from(request).get(S3Client)

    metadata = {}
    for prefix in all_prefixes:
        try:
            response = s3.list_objects_v2(Bucket=packet.s3_bucket_name, Prefix=prefix)
        except (BotoCoreError, ClientError):
            # we only need this for size / age, we're otherwise fine
            continue

        for object in response.get("Contents", []):
            metadata[object["Key"]] = PacketFileMetadata(
                object["LastModified"], object["Size"]
            )

    # Build display objects for all files
    def build_file_display(pf):
        display = PacketFileDisplay(pf, metadata.get(pf.s3_object_key))
        # Add access tracking info if member exists
        if member:
            # Use prefetched access records instead of querying
            prefetched_access = getattr(pf, "prefetched_member_access", [])
            if prefetched_access:
                access = prefetched_access[0]
                display.access_count = access.access_count
                display.has_code = (
                    pf.access_type == PacketFile.AccessType.CODE
                    and access.distribution_code is not None
                )
            else:
                display.access_count = 0
                display.has_code = False
        return display

    # Recursively build section hierarchy with files
    def build_section_tree(section):
        return {
            "section": section,
            "files": [build_file_display(f) for f in section.files.all()],
            "subsections": [build_section_tree(s) for s in section.subsections.all()],
        }

    section_tree = [build_section_tree(s) for s in root_sections]

    orphan_file_list = [build_file_display(pf) for pf in orphan_files]

    return render(
        request,
        "hugopacket/index.html",
        {
            "election": election,
            "packet": packet,
            "section_tree": section_tree,
            "orphan_files": orphan_file_list,
        },
    )


@login_required
@member_can_vote()
def download_packet(
    request: HttpRequest, election_id: str, packet_file_id: int
) -> HttpResponse:
    election = get_object_or_404(Election, slug=election_id)
    packet_file = get_object_or_404(PacketFile, pk=packet_file_id)
    # ensure that the packet file belongs to the election
    if packet_file.packet.election != election:
        raise Http404()

    if not packet_file.packet.enabled and not request.user.has_perm(
        "hugopacket.preview_packet"
    ):
        raise Http404()

    if not packet_file.available:
        return HttpResponseForbidden()

    # Get member profile (required for tracking access)
    member = request.user.convention_profile

    # Handle code-based access
    if packet_file.access_type == PacketFile.AccessType.CODE:
        # Get or create access record
        access, created = PacketItemAccess.objects.get_or_create(
            packet_file=packet_file, member=member
        )

        # Assign a code if not already assigned
        if not access.distribution_code:
            with transaction.atomic():
                # Get IDs of already assigned codes
                assigned_code_ids = PacketItemAccess.objects.filter(
                    distribution_code__packet_file=packet_file
                ).values_list("distribution_code_id", flat=True)

                # Find an unassigned code from the pool
                unassigned_code = (
                    DistributionCode.objects.filter(packet_file=packet_file)
                    .exclude(id__in=assigned_code_ids)
                    .select_for_update()
                    .first()
                )

                if not unassigned_code:
                    return render(
                        request,
                        "hugopacket/no_codes_available.html",
                        {"packet_file": packet_file},
                        status=503,
                    )

                # Assign the code
                access.distribution_code = unassigned_code
                unassigned_code.assigned_at = timezone.now()
                unassigned_code.save(update_fields=["assigned_at"])
                access.save(update_fields=["distribution_code"])

        # Record the access
        access.increment_access()

        # Format code for display and get raw version for copying
        raw_code = access.distribution_code.code
        display_code = packet_file.format_code(raw_code)

        # Display the code to the user
        return render(
            request,
            "hugopacket/display_code.html",
            {
                "packet_file": packet_file,
                "display_code": display_code,
                "copy_code": raw_code,
                "access_count": access.access_count,
            },
        )

    # Handle download-based access
    elif packet_file.access_type == PacketFile.AccessType.DOWNLOAD:
        # Get or create access record
        access, created = PacketItemAccess.objects.get_or_create(
            packet_file=packet_file, member=member
        )

        # Record the access
        access.increment_access()

        # Get presigned URL and redirect
        download_url = access.get_access_url(request)
        return redirect(download_url)

    else:
        raise ValueError(f"Unknown access type: {packet_file.access_type}")

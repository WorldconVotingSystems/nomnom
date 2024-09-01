from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse

from botocore.exceptions import BotoCoreError
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django_svcs.apps import svcs_from
from nomnom.nominate.models import Election

from nomnom.hugopacket.apps import S3Client
from nomnom.hugopacket.models import ElectionPacket, PacketFile


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

    all_prefixes = set()

    for packet_file in packet.packetfile_set.all():
        all_prefixes.add(packet_file.s3_object_key.rsplit("/", 1)[0])

    s3 = svcs_from(request).get(S3Client)

    metadata = {}
    for prefix in all_prefixes:
        try:
            response = s3.list_objects_v2(Bucket=packet.s3_bucket_name, Prefix=prefix)
        except BotoCoreError:
            # we only need this for size / age, we're otherwise fine
            continue

        for object in response.get("Contents", []):
            metadata[object["Key"]] = PacketFileMetadata(
                object["LastModified"], object["Size"]
            )

    packet_file_list = [
        PacketFileDisplay(pf, metadata.get(pf.s3_object_key))
        for pf in packet.packetfile_set.all()
    ]

    return render(
        request,
        "hugopacket/index.html",
        {
            "election": election,
            "packet": packet,
            "packet_files": packet_file_list,
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

    download_url = packet_file.get_download_url(request)
    return redirect(download_url)

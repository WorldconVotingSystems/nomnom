from dataclasses import dataclass
from datetime import datetime

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django_svcs.apps import svcs_from
from nominate.models import Election

from hugopacket.apps import S3Client
from hugopacket.models import ElectionPacket, PacketFile


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

    def __str__(self):
        return self.packet_file.name


def index(request: HttpRequest, election_id: str) -> HttpResponse:
    election = get_object_or_404(Election, slug=election_id)
    packet = get_object_or_404(ElectionPacket, election=election)

    # TODO get the size and modification time of the packet files; we
    # will do this by:
    # - finding all of the prefixes of the packet files (the directory part of their key)
    # - listing all files in those prefixes, storing them keyed by full key
    # - for each packet file, mark it up with the size and modification time by
    #   creating a wrapper object for it that adds those attributes but isn't DB-backed
    all_prefixes = set()

    for packet_file in packet.packetfile_set.all():
        all_prefixes.add(packet_file.s3_object_key.rsplit("/", 1)[0])

    s3 = svcs_from(request).get(S3Client)

    metadata = {}
    for prefix in all_prefixes:
        response = s3.list_objects_v2(Bucket=packet.s3_bucket_name, Prefix=prefix)
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


def download_packet(
    request: HttpRequest, election_id: str, packet_file_id: int
) -> HttpResponse:
    election = get_object_or_404(Election, slug=election_id)
    packet_file = get_object_or_404(PacketFile, pk=packet_file_id)

    # ensure that the packet file belongs to the election
    if packet_file.packet.election != election:
        raise Http404()

    return redirect(packet_file.get_download_url(request))

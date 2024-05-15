from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from nominate.models import Election

from hugopacket.models import ElectionPacket, PacketFile


def index(request: HttpRequest, election_id: str) -> HttpResponse:
    election = get_object_or_404(Election, slug=election_id)
    packet = get_object_or_404(ElectionPacket, election=election)
    return render(
        request,
        "hugopacket/index.html",
        {
            "election": election,
            "packet": packet,
            "packet_files": packet.packetfile_set.all(),
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

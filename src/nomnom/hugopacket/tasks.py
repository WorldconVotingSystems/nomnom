from celery import shared_task
from celery.exceptions import Ignore
from celery.utils.log import get_task_logger
from django_svcs.apps import svcs_from

from nomnom.hugopacket.apps import S3Client

logger = get_task_logger(__name__)


@shared_task
def refresh_all_packet_size_data(packet_id: int):
    """Recalculate size data for all packet files in the given packet."""
    from .models import ElectionPacket, PacketFile

    packet = ElectionPacket.objects.get(pk=packet_id)
    for pf in packet.packetfile_set.filter(access_type=PacketFile.AccessType.DOWNLOAD):
        refresh_packet_file_size_data.delay(packet_file_id=pf.id)


@shared_task(bind=True)
def refresh_packet_file_size_data(self, packet_file_id: int):
    """Recalculate size data for a single packet file."""
    from .models import PacketFile

    try:
        pf = PacketFile.objects.get(pk=packet_file_id)
    except PacketFile.DoesNotExist:
        logger.warning("PacketFile with id=%d does not exist", packet_file_id)
        raise Ignore()

    if refreshed := pf.get_file_metadata(svcs_from().get(S3Client)):  # noqa: F841
        pf.save()
    else:
        # mark the task as failed
        logger.warning(
            "Failed to refresh size data for PacketFile id=%d", packet_file_id
        )
        return

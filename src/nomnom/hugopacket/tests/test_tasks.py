from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from celery.exceptions import Ignore
from django_svcs.apps import get_registry

from nomnom.hugopacket.apps import S3Client
from nomnom.hugopacket.models import ElectionPacket, PacketFile
from nomnom.hugopacket.tasks import (
    refresh_all_packet_size_data,
    refresh_packet_file_size_data,
)
from nomnom.nominate.models import Election


class FakeNoSuchKey(Exception):
    pass


class FakeS3Exceptions:
    NoSuchKey = FakeNoSuchKey


class FakeS3Client:
    """Minimal fake S3 client for testing packet file metadata retrieval."""

    def __init__(self):
        self.exceptions = FakeS3Exceptions()
        self._head_object_response = None
        self._head_object_error = None

    def configure_head_object(self, response=None, error=None):
        self._head_object_response = response
        self._head_object_error = error

    def head_object(self, Bucket, Key):
        if self._head_object_error:
            raise self._head_object_error
        if self._head_object_response:
            return self._head_object_response
        raise FakeNoSuchKey(f"No such key: {Key}")

    def list_objects_v2(self, **kwargs):
        return {"Contents": []}

    def generate_presigned_url(self, *args, **kwargs):
        return "https://fake-s3-url.example.com/file.pdf"


@pytest.fixture
def mock_s3_client():
    """Override conftest's mock_s3_client: register FakeS3Client and clear cached container."""
    client = FakeS3Client()
    registry = get_registry()
    registry.register_value(S3Client, client)

    # TODO: this should be handled in django-svcs, which I also maintain,
    # but doesn't currently offer the right behaviour. I'm not sure
    # what it should be, yet, but it's clearly wrong here.
    #
    # Anyway, this ugly bit of internals hacking does what we need for testing.
    from django_svcs.apps import _KEY_CONTAINER, _NON_REQUEST_CONTEXT

    # Clear any cached container so svcs_from() picks up the new registration
    try:
        delattr(_NON_REQUEST_CONTEXT, _KEY_CONTAINER)
    except AttributeError:
        pass
    yield client
    try:
        delattr(_NON_REQUEST_CONTEXT, _KEY_CONTAINER)
    except AttributeError:
        pass


@pytest.fixture
def election(db):
    election = Election.objects.create(slug="test-2025", name="Test 2025")
    election.state = Election.STATE.VOTING
    election.save()
    return election


@pytest.fixture
def packet(db, election):
    return ElectionPacket.objects.create(
        election=election,
        name="Test Packet",
        s3_bucket_name="test-bucket",
        enabled=True,
    )


@pytest.fixture
def download_file(packet):
    return PacketFile.objects.create(
        packet=packet,
        name="Download File",
        access_type=PacketFile.AccessType.DOWNLOAD,
        s3_object_key="files/novel.epub",
        position=0,
    )


@pytest.fixture
def code_file(packet):
    return PacketFile.objects.create(
        packet=packet,
        name="Code File",
        access_type=PacketFile.AccessType.CODE,
        position=1,
    )


@pytest.mark.django_db
@pytest.mark.usefixtures("mock_s3_client")
class TestRefreshAllPacketSizeData:
    def test_dispatches_tasks_for_download_files_only(
        self, packet, download_file, code_file
    ):
        with patch(
            "nomnom.hugopacket.tasks.refresh_packet_file_size_data"
        ) as mock_task:
            refresh_all_packet_size_data(packet.id)

            mock_task.delay.assert_called_once_with(packet_file_id=download_file.id)

    def test_no_tasks_when_no_download_files(self, packet, code_file):
        with patch(
            "nomnom.hugopacket.tasks.refresh_packet_file_size_data"
        ) as mock_task:
            refresh_all_packet_size_data(packet.id)

            mock_task.delay.assert_not_called()


@pytest.mark.django_db
class TestRefreshPacketFileSizeData:
    def test_updates_metadata_on_success(self, download_file, mock_s3_client):
        last_modified = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_s3_client.configure_head_object(
            response={
                "ContentLength": 12345,
                "LastModified": last_modified,
            }
        )

        refresh_packet_file_size_data(packet_file_id=download_file.id)

        download_file.refresh_from_db()
        assert download_file.size == 12345
        assert download_file.last_modified == last_modified

    def test_raises_ignore_when_file_not_found(self):
        with pytest.raises(Ignore):
            refresh_packet_file_size_data(packet_file_id=99999)

    def test_does_not_save_on_s3_failure(self, download_file):
        # Default FakeS3Client raises NoSuchKey
        refresh_packet_file_size_data(packet_file_id=download_file.id)

        download_file.refresh_from_db()
        assert download_file.size is None


@pytest.mark.django_db
class TestGetFileMetadata:
    def test_returns_true_and_sets_fields_on_success(self, download_file):
        last_modified = datetime(2025, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
        client = FakeS3Client()
        client.configure_head_object(
            response={
                "ContentLength": 67890,
                "LastModified": last_modified,
            }
        )

        result = download_file.get_file_metadata(client)

        assert result is True
        assert download_file.size == 67890
        assert download_file.last_modified == last_modified

    def test_returns_false_on_no_such_key(self, download_file):
        client = FakeS3Client()
        # Default behaviour is NoSuchKey

        result = download_file.get_file_metadata(client)

        assert result is False
        assert download_file.size is None

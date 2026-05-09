import pytest
from unittest.mock import MagicMock

from django_svcs.apps import get_registry

from nomnom.hugopacket.apps import PacketAccess, S3Client


@pytest.fixture(autouse=True)
def mock_s3_client():
    """Register fake S3 services in the svcs registry for all hugopacket tests."""
    registry = get_registry()

    mock_client = MagicMock()
    mock_client.list_objects_v2.return_value = {"Contents": []}
    mock_client.generate_presigned_url.return_value = (
        "https://fake-s3-url.example.com/file.pdf"
    )

    mock_access = MagicMock(spec=PacketAccess)
    mock_resolver = MagicMock()
    mock_resolver.get_url.return_value = "https://fake-s3-url.example.com/file.pdf"
    mock_access.resolver.return_value = mock_resolver

    registry.register_value(S3Client, mock_client)
    registry.register_value(PacketAccess, mock_access)

    yield mock_client

    # Clean up by re-registering the factories (the app will re-register on next ready)
    # For tests this is fine since each test gets a fresh registry state via autouse

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_s3_client():
    """Automatically mock S3 client for all hugopacket tests."""
    # Create a mock S3 client
    mock_client = MagicMock()

    # Mock list_objects_v2 to return empty results
    mock_client.list_objects_v2.return_value = {"Contents": []}

    # Mock generate_presigned_url to return a fake URL
    mock_client.generate_presigned_url.return_value = (
        "https://fake-s3-url.example.com/file.pdf"
    )

    # Patch svcs_from().get() to return our mock when S3Client is requested
    # Import S3Client type from apps
    from nomnom.hugopacket.apps import S3Client

    # Create a mock container that returns our mock_client for S3Client
    mock_container = MagicMock()

    def mock_get(service_type):
        if service_type == S3Client:
            return mock_client
        # For other service types, call the original get
        raise NotImplementedError(f"Mock doesn't handle {service_type}")

    mock_container.get = mock_get

    # Patch svcs_from to return our mock container
    with patch("nomnom.hugopacket.views.svcs_from", return_value=mock_container):
        yield mock_client

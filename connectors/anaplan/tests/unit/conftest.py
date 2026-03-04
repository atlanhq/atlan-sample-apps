from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_objectstore_download():
    """Prevent real Dapr ObjectStore calls during unit tests."""
    with patch(
        "application_sdk.services.objectstore.ObjectStore.download_file",
        new_callable=AsyncMock,
    ) as mock:
        yield mock

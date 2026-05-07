"""Dev server for the Generic Connector.

Usage:
    # 1. Start Temporal dev server (in a separate terminal):
    temporal server start-dev --dynamic-config-value frontend.WorkerHeartbeatsEnabled=true

    # 2. Start the dev server:
    python -m app.run_dev

    # 3. Trigger a test workflow:
    curl -X POST http://localhost:8000/workflows/v1/start \\
      -H "Content-Type: application/json" \\
      -d '{
        "connection": {"qualifiedName": "default/generic/test", "name": "test"},
        "source": "https://example.com/data",
        "load_to_atlan": false
      }'

    # 4. Check the result (replace <workflow_id> with value from start response):
    curl http://localhost:8000/workflows/v1/result/<workflow_id>
"""

import asyncio

from app.connector import GenericConnector
from application_sdk.main import run_dev_combined


async def main() -> None:
    await run_dev_combined(
        GenericConnector,
        example_input={
            "connection": {
                "qualifiedName": "default/generic/test",
                "name": "test",
            },
            "source": "https://example.com/data",
            "load_to_atlan": False,
        },
    )


if __name__ == "__main__":
    asyncio.run(main())

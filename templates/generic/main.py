"""Entry point for the Generic Connector app.

For local development with curl examples, use ``app/run_dev.py`` instead.
"""

import asyncio

from app.run_dev import main

if __name__ == "__main__":
    asyncio.run(main())

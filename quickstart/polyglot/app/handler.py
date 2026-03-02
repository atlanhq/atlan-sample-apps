"""Handler for Polyglot application."""

import json
from pathlib import Path
from typing import Any, Dict

from application_sdk.handlers.base import BaseHandler


class PolyglotHandler(BaseHandler):
    """Handler for Polyglot application."""

    @staticmethod
    async def get_configmap(config_map_id: str) -> Dict[str, Any]:
        """Get configuration map for the application.

        Args:
            config_map_id: ID of the config map to retrieve

        Returns:
            Dictionary containing the configuration
        """
        config_path = Path().cwd() / "frontend" / "static" / "config.json"

        with open(config_path) as f:
            return json.load(f)

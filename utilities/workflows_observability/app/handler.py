from pathlib import Path
from typing import Any, Dict

import yaml
from application_sdk.handlers.base import BaseHandler
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class WorkflowsObservabilityHandler(BaseHandler):
    @staticmethod
    async def get_uiconfig(config_name: str) -> Dict[str, Any]:
        """
        Get UI configuration for Workflows Observability app.

        Args:
            config_name: The UI config name (e.g. 'workflows-observability')

        Returns:
            Dict containing the UI configuration data
        """
        uiconfig_path = Path().cwd() / "app" / "uiconfigs" / "default.yaml"

        with open(uiconfig_path) as f:
            return yaml.safe_load(f)

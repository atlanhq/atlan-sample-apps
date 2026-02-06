import json
import os
from pathlib import Path
from typing import Any, Dict

from application_sdk.clients.sql import BaseSQLClient
from application_sdk.common.utils import read_sql_files
from application_sdk.constants import SQL_QUERIES_PATH
from application_sdk.handlers.sql import BaseSQLHandler
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)

DEPLOYMENT_TYPE_PROVISIONED = "provisioned"
DEPLOYMENT_TYPE_SERVERLESS = "serverless"


class RedshiftHandler(BaseSQLHandler):
    """
    Handler for Redshift
    """

    def __init__(self, sql_client: BaseSQLClient | None = None):
        if str(os.getenv("ATLAN_ENABLE_REDSHIFT_MINER", "true")).lower() == "true":
            multidb = False
        else:
            multidb = True
        super().__init__(sql_client, multidb=multidb)

        queries = read_sql_files(queries_prefix=SQL_QUERIES_PATH)

        # Miner-specific privilege checks (always loaded)
        self.miner_check_provisioned_sql = queries.get("MINER_CHECK_PROVISIONED")
        self.miner_check_serverless_sql = queries.get("MINER_CHECK_SERVERLESS")

        # Tables check sql for miner (only when miner enabled)
        if not self.multidb:
            self.tables_check_sql = queries.get("TABLES_CHECK_MINER")

    @staticmethod
    async def get_configmap(config_map_id: str) -> Dict[str, Any]:
        workflow_json_path = Path().cwd() / "app" / "templates" / "workflow.json"
        credential_json_path = (
            Path().cwd() / "app" / "templates" / "atlan-connectors-redshift.json"
        )

        if config_map_id == "atlan-connectors-redshift":
            with open(credential_json_path) as f:
                return json.load(f)

        with open(workflow_json_path) as f:
            return json.load(f)

    # -----------------------------
    # Miner preflight (query history)
    # -----------------------------
    def _get_deployment_type(self, payload: Dict[str, Any]) -> str:
        """Extract and validate deployment_type from payload; default to provisioned."""
        try:
            value = payload["credentials"]["extra"]["deployment_type"]
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in (
                    DEPLOYMENT_TYPE_PROVISIONED,
                    DEPLOYMENT_TYPE_SERVERLESS,
                ):
                    return normalized
        except (KeyError, TypeError):
            pass
        return DEPLOYMENT_TYPE_PROVISIONED

    def _get_system_tables(self) -> Dict[str, str]:
        """Return all system table names for miner checks. Callers use keys per deployment type."""
        return {
            # Serverless (SYS_* views)
            "queryHistory": "sys_query_history",
            "queryText": "sys_query_text",
            "connectionLog": "sys_connection_log",
            # Provisioned (SVL/STL tables - matches extract_query_provisioned.sql)
            "statementTextProvisioned": "svl_statementtext",
            "connectionLogProvisioned": "stl_connection_log",
        }

    async def _check_table_privilege(
        self, deployment_type: str, table_name: str
    ) -> Dict[str, Any]:
        """
        Determines check strategy from deployment_type:
        - serverless: run SELECT 1 FROM {table_name} LIMIT 1
        - provisioned: run SELECT has_table_privilege('{table_name}','select') AS has_table_privilege
        Returns a dict with success/successMessage/failureMessage/error (aligned to BaseSQLHandler checks).
        """
        try:
            if deployment_type == DEPLOYMENT_TYPE_SERVERLESS:
                if not self.miner_check_serverless_sql:
                    raise ValueError("MINER_CHECK_SERVERLESS query not found")
                query = self.miner_check_serverless_sql.format(table_name=table_name)
                await self.sql_client.get_results(query)
                return {
                    "success": True,
                    "successMessage": f"Permission validated for {table_name}",
                    "failureMessage": "",
                }
            else:
                if not self.miner_check_provisioned_sql:
                    raise ValueError("MINER_CHECK_PROVISIONED query not found")
                query = self.miner_check_provisioned_sql.format(table_name=table_name)
                df = await self.sql_client.get_results(query)
                row = next(iter(df.to_dict(orient="records")), {})
                if bool(row.get("has_table_privilege")):
                    return {
                        "success": True,
                        "successMessage": f"Permission validated for {table_name}",
                        "failureMessage": "",
                    }
                return {
                    "success": False,
                    "successMessage": "",
                    "failureMessage": f"Missing SELECT permission on {table_name}",
                }
        except Exception as exc:
            logger.error("Access check failed for table %s", table_name)
            return {
                "success": False,
                "successMessage": "",
                "failureMessage": f"Access check failed for {table_name}",
                "error": str(exc),
            }

    async def _miner_preflight_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run miner preflight checks for query_history extraction.
        Validates access to system tables based on deployment type.
        """
        deployment_type = self._get_deployment_type(payload)
        tables = self._get_system_tables()

        if deployment_type == DEPLOYMENT_TYPE_SERVERLESS:
            checks: Dict[str, Any] = {
                "queryHistoryCheck": await self._check_table_privilege(
                    deployment_type, tables["queryHistory"]
                ),
                "queryTextCheck": await self._check_table_privilege(
                    deployment_type, tables["queryText"]
                ),
                "connectionLogCheck": await self._check_table_privilege(
                    deployment_type, tables["connectionLog"]
                ),
            }
        else:
            checks: Dict[str, Any] = {
                "statementTextCheck": await self._check_table_privilege(
                    deployment_type, tables["statementTextProvisioned"]
                ),
                "connectionLogCheck": await self._check_table_privilege(
                    deployment_type, tables["connectionLogProvisioned"]
                ),
            }

        if all(item.get("success") for item in checks.values()):
            logger.info("Miner preflight checks completed successfully")
        else:
            failed = [name for name, r in checks.items() if not r.get("success")]
            logger.warning("Miner preflight checks failed for: %s", failed)

        return checks

    async def preflight_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        If extraction-method == query_history => run miner preflight checks
        Else fall back to normal SQL preflight.
        """
        metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
        if metadata.get("extraction-method", "direct") == "query_history":
            logger.info("Running Redshift miner preflight checks (query_history)")
            return await self._miner_preflight_check(payload)

        return await super().preflight_check(payload)

"""Handler for the Generic Connector.

Implements the three HTTP service operations that run *before* a workflow
starts: auth testing, preflight checks, and metadata discovery.

The SDK auto-discovers ``GenericConnectorHandler`` because it is imported
in ``connector.py`` (same module as ``GenericConnector``).  You can also
point to it explicitly via ``ATLAN_HANDLER_MODULE=app.handler:GenericConnectorHandler``.

Replace the pass-through stubs below with logic specific to your source system.
"""

from __future__ import annotations

from application_sdk.handler import (
    ApiMetadataOutput,
    AuthInput,
    AuthOutput,
    AuthStatus,
    DefaultHandler,
    MetadataInput,
    PreflightInput,
    PreflightOutput,
    PreflightStatus,
)


class GenericConnectorHandler(DefaultHandler):
    """Handler for the Generic Connector HTTP service.

    Override the methods below to add real auth testing, preflight checks,
    and metadata browsing for your source system.
    """

    async def test_auth(self, input: AuthInput) -> AuthOutput:
        """Verify that the provided credentials can reach the source system.

        TODO: replace with real connectivity check.

        Example (HTTP source)::

            import httpx
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        input.connection_config.get("host", ""),
                        headers={"Authorization": input.credentials[0].token if input.credentials else ""},
                        timeout=5.0,
                    )
                resp.raise_for_status()
                return AuthOutput(status=AuthStatus.SUCCESS)
            except Exception as exc:
                return AuthOutput(status=AuthStatus.FAILED, message=str(exc))
        """
        return AuthOutput(
            status=AuthStatus.SUCCESS,
            message="Authentication successful",
        )

    async def preflight_check(self, input: PreflightInput) -> PreflightOutput:
        """Run pre-workflow checks (permissions, connectivity, required fields).

        TODO: replace with checks specific to your source system.

        Example::

            issues = []
            if not input.connection_config.get("host"):
                issues.append("host is required")
            if issues:
                return PreflightOutput(
                    status=PreflightStatus.FAILED,
                    message="; ".join(issues),
                )
            return PreflightOutput(status=PreflightStatus.READY)
        """
        return PreflightOutput(
            status=PreflightStatus.READY,
            message="All preflight checks passed",
        )

    async def fetch_metadata(self, input: MetadataInput) -> ApiMetadataOutput:
        """Return a browsable tree of objects from the source system.

        Used by the Atlan UI apitree browser widget.

        TODO: replace with real resource discovery.

        Example::

            resources = await my_client.list_resources()
            return ApiMetadataOutput(
                objects=[
                    ApiMetadataObject(
                        value=r.id,
                        title=r.name,
                        node_type="resource",
                        children=[
                            ApiMetadataObject(value=f.id, title=f.name, node_type="field")
                            for f in r.fields
                        ],
                    )
                    for r in resources
                ]
            )
        """
        return ApiMetadataOutput(objects=[])

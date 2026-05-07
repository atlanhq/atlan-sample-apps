"""Generic Connector App.

Replace the placeholder tasks and orchestration with your connector logic.

Extraction pattern: sequential — extract raw records, then transform to
Atlan asset format.  Adapt to your source data shape and asset types.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.contracts import (
    ExtractInput,
    ExtractOutput,
    GenericConnectorInput,
    GenericConnectorOutput,
    TransformInput,
    TransformOutput,
)

from application_sdk.app import App, task
from application_sdk.contracts.storage import UploadInput
from application_sdk.contracts.types import FileReference, StorageTier
from application_sdk.errors import InvalidInputError


class GenericConnector(App):
    """Generic connector scaffold.

    Replace the @task methods and run() below with your connector logic.
    See https://github.com/atlanhq/application-sdk for full reference.
    """

    name = "generic"

    @task(
        timeout_seconds=1800,
        heartbeat_timeout_seconds=120,
        auto_heartbeat_seconds=30,
    )
    async def extract(self, input: ExtractInput) -> ExtractOutput:
        """Fetch source data and write raw records to a JSONL file.

        TODO: replace the placeholder with real extraction logic.
        - Fetch data from input.source (URL, DB connection, API, etc.)
        - Write one JSON object per line to output_file
        """
        out_dir = Path(input.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        output_file = out_dir / "raw.jsonl"

        self.logger.info("extract task starting source=%s", input.source)

        # TODO: implement extraction here.
        # Example (HTTP):
        #   import httpx, json
        #   async with httpx.AsyncClient() as client:
        #       response = await client.get(input.source)
        #       records = response.json()
        #   with output_file.open("w") as f:
        #       for record in records:
        #           f.write(json.dumps(record) + "\n")

        output_file.write_text("")  # placeholder — remove when implemented
        record_count = 0

        self.logger.info("extract task completed record_count=%d", record_count)
        return ExtractOutput(
            output_file=FileReference(
                local_path=str(output_file), tier=StorageTier.RETAINED
            ),
            record_count=record_count,
        )

    @task(
        timeout_seconds=1800,
        heartbeat_timeout_seconds=120,
        auto_heartbeat_seconds=30,
    )
    async def transform(self, input: TransformInput) -> TransformOutput:
        """Map raw records to Atlan Atlas entity format.

        TODO: replace the placeholder with real transformation logic.
        - Read raw records from input.raw_file.local_path
        - Map each record to a pyatlan asset type (Table, Column, etc.)
        - Write serialized assets to output_file as JSONL
        """
        out_dir = Path(input.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        output_file = out_dir / "assets.jsonl"

        self.logger.info("transform task starting")

        if input.raw_file is None or not input.raw_file.local_path:
            self.logger.warning(
                "transform called with no raw_file; writing empty output"
            )
            output_file.write_text("")
            return TransformOutput(
                output_file=FileReference(
                    local_path=str(output_file), tier=StorageTier.RETAINED
                ),
                record_count=0,
            )

        # TODO: implement transformation here.
        # Example (pyatlan mapping):
        #   import json
        #   from pyatlan.model.assets import Table
        #   with open(input.raw_file.local_path) as raw_f, output_file.open("wb") as out_f:
        #       for line in raw_f:
        #           raw = json.loads(line)
        #           asset = Table(
        #               qualified_name=f"{input.connection_qualified_name}/{raw['name']}",
        #               name=raw["name"],
        #           )
        #           out_f.write(asset.to_nested_bytes() + b"\n")

        output_file.write_text("")  # placeholder — remove when implemented
        record_count = 0

        self.logger.info("transform task completed record_count=%d", record_count)
        return TransformOutput(
            output_file=FileReference(
                local_path=str(output_file), tier=StorageTier.RETAINED
            ),
            record_count=record_count,
        )

    async def run(self, input: GenericConnectorInput) -> GenericConnectorOutput:
        """Orchestrate the connector workflow.

        Steps:
        1. Validate required inputs
        2. extract  — fetch source data, write raw JSONL
        3. transform — map raw records to Atlan asset format
        4. upload + publish to Atlan (when load_to_atlan=True)
        """
        connection = self.require(input.connection, "connection")
        conn_qn = connection.attributes.qualified_name

        if not input.source:
            raise InvalidInputError(
                message="source is required",
                field="source",
                constraint="required",
            )

        output_dir = input.output_dir or str(
            Path(tempfile.gettempdir()) / "generic" / self.run_id
        )

        self.logger.info(
            "generic connector starting connection_qualified_name=%s source=%s load_to_atlan=%s",
            conn_qn,
            input.source,
            input.load_to_atlan,
        )

        # Step 1: Extract raw data
        extract_result = await self.extract(
            ExtractInput(
                source=input.source,
                output_dir=f"{output_dir}/raw",
            )
        )

        record_count = 0
        output_file_ref = None
        transformed_data_prefix = ""

        if extract_result.record_count > 0:
            # Step 2: Transform to Atlan asset format
            transform_result = await self.transform(
                TransformInput(
                    raw_file=extract_result.output_file,
                    connection_qualified_name=conn_qn,
                    output_dir=f"{output_dir}/transform",
                    workflow_id=self.run_id,
                )
            )
            record_count = transform_result.record_count
            output_file_ref = transform_result.output_file

            # Step 3: Upload to object storage for publish-app consumption
            if input.load_to_atlan and output_file_ref and output_file_ref.local_path:
                upload_result = await self.upload(
                    UploadInput(
                        local_path=output_file_ref.local_path,
                        storage_path=(
                            f"artifacts/apps/{self.context.app_name}/workflows/"
                            f"{self.run_id}/transformed/"
                            f"{Path(output_file_ref.local_path).name}"
                        ),
                    )
                )
                if upload_result.ref.storage_path:
                    transformed_data_prefix = str(
                        Path(upload_result.ref.storage_path).parent
                    )

        self.logger.info(
            "generic connector completed record_count=%d",
            record_count,
        )

        return GenericConnectorOutput(
            connection_qualified_name=conn_qn,
            transformed_data_prefix=transformed_data_prefix,
            record_count=record_count,
            output_file=output_file_ref,
        )

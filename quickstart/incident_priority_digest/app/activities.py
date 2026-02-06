import json
import os
from typing import Any, Dict, List

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

from .digest import build_digest

logger = get_logger(__name__)
activity.logger = logger


class IncidentDigestActivities(ActivitiesInterface):
    @activity.defn
    async def parse_records(
        self, workflow_args: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Parse incident records from the workflow args ``records_json`` field.

        Accepts either a JSON string or a pre-parsed list.
        """
        raw = workflow_args.get("records_json", "[]")
        if isinstance(raw, str):
            records = json.loads(raw)
        else:
            records = raw

        logger.info(f"Parsed {len(records)} incident records")
        return records

    @activity.defn
    async def write_raw_output(self, args: Dict[str, Any]) -> str:
        """Write the raw incident records to the ``raw/incidents`` output path.

        Returns the path where the file was written.
        """
        output_path = args["output_path"]
        records: List[Dict[str, Any]] = args["records"]

        raw_dir = os.path.join(output_path, "raw", "incidents")
        os.makedirs(raw_dir, exist_ok=True)

        raw_file = os.path.join(raw_dir, "incidents.json")
        with open(raw_file, "w") as f:
            json.dump(records, f, indent=2)

        logger.info(f"Wrote {len(records)} raw records to {raw_file}")
        return raw_file

    @activity.defn
    async def generate_and_write_digest(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Build the digest and write it to ``transformed/digest``.

        Returns the digest payload.
        """
        output_path = args["output_path"]
        records: List[Dict[str, Any]] = args["records"]

        digest = build_digest(records)

        transformed_dir = os.path.join(output_path, "transformed", "digest")
        os.makedirs(transformed_dir, exist_ok=True)

        digest_file = os.path.join(transformed_dir, "digest.json")
        with open(digest_file, "w") as f:
            json.dump(digest, f, indent=2)

        logger.info(
            f"Wrote digest with {digest['total_incidents']} incidents to {digest_file}"
        )
        return digest

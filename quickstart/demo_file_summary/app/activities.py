import json
from collections import Counter
from typing import Any, Dict, List

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows.object_store_client import ObjectStoreClient
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


class FileSummaryActivities(ActivitiesInterface):
    @activity.defn
    async def summarize_status_counts(
        self, workflow_config: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Read JSON input from object store, count status occurrences,
        and write summary to object store.

        Args:
            workflow_config: Workflow configuration containing input/output file paths

        Returns:
            Dictionary with status counts
        """
        logger.info("Starting status count summarization")

        # Initialize object store client
        object_store = ObjectStoreClient(logger=logger)

        # Get input file path from workflow config
        input_path = workflow_config.get("input_file", "input/records.json")
        output_path = workflow_config.get("output_file", "output/summary.json")

        try:
            # Read input JSON from object store
            logger.info(f"Reading input from: {input_path}")
            input_data = await object_store.get(input_path)

            # Parse JSON
            records: List[Dict[str, Any]] = json.loads(input_data)
            logger.info(f"Loaded {len(records)} records")

            # Count status occurrences
            status_list = [record.get("status", "unknown") for record in records]
            status_counts = dict(Counter(status_list))

            logger.info(f"Status counts: {status_counts}")

            # Prepare summary output
            summary = {
                "total_records": len(records),
                "status_counts": status_counts,
            }

            # Write summary to object store
            logger.info(f"Writing summary to: {output_path}")
            await object_store.set(output_path, json.dumps(summary, indent=2))

            logger.info("Status count summarization completed successfully")
            return status_counts

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON input: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during status summarization: {e}")
            raise

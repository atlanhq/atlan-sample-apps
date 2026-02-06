import asyncio

from application_sdk.application.metadata_extraction.sql import (
    BaseSQLMetadataExtractionApplication,
)
from application_sdk.constants import APPLICATION_NAME

from app.activities.metadata_extraction.redshift import (
    RedshiftSQLMetadataExtractionActivities,
)
from app.activities.query_extraction.redshift import RedshiftQueryExtractionActivities
from app.clients import RedshiftClient
from app.handlers.redshift import RedshiftHandler
from app.transformers.query import RedshiftQueryBasedTransformer
from app.workflows.metadata_extraction.redshift import (
    RedshiftMetadataExtractionWorkflow,
)
from app.workflows.query_extraction.redshift import RedshiftQueryExtractionWorkflow


async def main():
    application = BaseSQLMetadataExtractionApplication(
        name=APPLICATION_NAME,
        client_class=RedshiftClient,
        handler_class=RedshiftHandler,
        transformer_class=RedshiftQueryBasedTransformer,  # type: ignore
    )
    await application.setup_workflow(
        workflow_and_activities_classes=[
            (
                RedshiftMetadataExtractionWorkflow,
                RedshiftSQLMetadataExtractionActivities,
            ),
            (RedshiftQueryExtractionWorkflow, RedshiftQueryExtractionActivities),
        ]
    )

    await application.start(
        workflow_class=RedshiftMetadataExtractionWorkflow, has_configmap=True
    )


if __name__ == "__main__":
    asyncio.run(main())

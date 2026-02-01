import asyncio
from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import AccessibilityAuditActivities
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow
from temporalio.common import RetryPolicy

logger = get_logger(__name__)
workflow.logger = logger
metrics = get_metrics()
traces = get_traces()


@workflow.defn
class AccessibilityAuditWorkflow(WorkflowInterface):
    @observability(logger=logger, metrics=metrics, traces=traces)
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """
        This workflow performs an accessibility audit on a given URL.

        It uses both axe-core (via Playwright) and WAVE API to provide
        comprehensive accessibility testing results.

        Args:
            workflow_config (Dict[str, Any]): The workflow configuration

        Returns:
            None
        """
        activities_instance = AccessibilityAuditActivities()

        retry_policy = RetryPolicy(
            maximum_attempts=3,
            backoff_coefficient=2,
        )

        # Get the workflow configuration from the state store
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_config,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(seconds=30),
        )

        target_url: str = workflow_args.get("url", "")
        wave_api_key: str = workflow_args.get("wave_api_key", "")
        wcag_level: str = workflow_args.get("wcag_level", "AA")

        if not target_url:
            logger.error("No target URL provided for accessibility audit")
            return

        logger.info(f"Starting accessibility audit for: {target_url}")

        # Run both audits in parallel for efficiency
        audit_tasks = [
            workflow.execute_activity_method(
                activities_instance.run_axe_audit,
                {"url": target_url, "wcag_level": wcag_level},
                retry_policy=retry_policy,
                start_to_close_timeout=timedelta(seconds=120),
            ),
        ]

        # Only run WAVE audit if API key is provided
        if wave_api_key:
            audit_tasks.append(
                workflow.execute_activity_method(
                    activities_instance.run_wave_audit,
                    {"url": target_url, "api_key": wave_api_key},
                    retry_policy=retry_policy,
                    start_to_close_timeout=timedelta(seconds=60),
                )
            )

        # Wait for all audit activities to complete
        results = await asyncio.gather(*audit_tasks)

        axe_results = results[0]
        wave_results = results[1] if len(results) > 1 else None

        # Generate combined report
        await workflow.execute_activity_method(
            activities_instance.generate_report,
            {
                "url": target_url,
                "axe_results": axe_results,
                "wave_results": wave_results,
                "wcag_level": wcag_level,
            },
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(seconds=30),
        )

        logger.info("Accessibility audit workflow completed")

    @staticmethod
    def get_activities(activities: ActivitiesInterface) -> Sequence[Callable[..., Any]]:
        """Get the sequence of activities to be executed by the workflow.

        Args:
            activities (ActivitiesInterface): The activities instance
                containing the accessibility audit operations.

        Returns:
            Sequence[Callable[..., Any]]: A sequence of activity methods to be executed.
        """
        if not isinstance(activities, AccessibilityAuditActivities):
            raise TypeError(
                "Activities must be an instance of AccessibilityAuditActivities"
            )

        return [
            activities.get_workflow_args,
            activities.run_axe_audit,
            activities.run_wave_audit,
            activities.generate_report,
        ]

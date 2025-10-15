"""Workflow for the polyglot sample app.

This module defines the Temporal workflow that orchestrates polyglot
(Python-Java) activities.
"""

from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import PolyglotActivities
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow

logger = get_logger(__name__)
workflow.logger = logger
metrics = get_metrics()
traces = get_traces()


@workflow.defn
class PolyglotWorkflow(WorkflowInterface):
    """Workflow demonstrating polyglot programming (Python-Java integration).

    This workflow orchestrates activities that call Java methods from Python
    code using JPype, showcasing cross-language integration patterns.
    """

    @observability(logger=logger, metrics=metrics, traces=traces)
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the Polyglot workflow.

        Args:
            workflow_config: The workflow configuration containing:
                - workflow_id: Unique identifier for this workflow
                - number: Number to calculate factorial for

        Returns:
            Dict[str, Any]: Workflow execution results including:
                - calculation_result: Result of factorial calculation
                - status: Overall workflow status

        Example:
            >>> config = {
            ...     'workflow_id': 'polyglot-123',
            ...     'number': 5
            ... }
            >>> result = await workflow.execute_workflow(
            ...     PolyglotWorkflow.run,
            ...     config
            ... )
        """
        activities_instance = PolyglotActivities()

        logger.info(f"Starting polyglot workflow with config: {workflow_config}")

        # Get workflow configuration from the state store
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Extract number parameter
        number = workflow_args.get("number", 5)  # Default to 5

        logger.info(f"Calculating factorial for number: {number}")

        # Calculate factorial using Java
        calculation_result = await workflow.execute_activity_method(
            activities_instance.calculate_factorial,
            number,
            start_to_close_timeout=timedelta(seconds=10),
        )

        logger.info(f"Calculation result: {calculation_result}")

        # Save result to JSON file
        output_path = workflow_args.get("output_path", "/tmp/polyglot")
        calculation_result["output_path"] = output_path
        save_stats = await workflow.execute_activity_method(
            activities_instance.save_result_to_json,
            calculation_result,
            start_to_close_timeout=timedelta(seconds=10),
        )

        logger.info(f"Save statistics: {save_stats}")

        # Prepare final result
        result = {
            "calculation_result": calculation_result,
            "save_stats": save_stats,
            "status": "success" if calculation_result.get("success") else "failed",
        }

        logger.info("Polyglot workflow completed successfully")
        return result

    @staticmethod
    def get_activities(activities: ActivitiesInterface) -> Sequence[Callable[..., Any]]:
        """Get the sequence of activities to be executed by the workflow.

        Args:
            activities: The activities instance containing the polyglot operations.

        Returns:
            Sequence[Callable[..., Any]]: A sequence of activity methods to be
                executed by the workflow.

        Raises:
            TypeError: If activities is not an instance of PolyglotActivities.
        """
        if not isinstance(activities, PolyglotActivities):
            raise TypeError("Activities must be an instance of PolyglotActivities")

        return [
            activities.calculate_factorial,
            activities.save_result_to_json,
            activities.get_workflow_args,
        ]

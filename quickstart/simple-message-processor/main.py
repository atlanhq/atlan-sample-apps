"""Simple Message Processor Application.

This application demonstrates how to use the application-sdk MessageProcessor
to process messages from Kafka in batches without Temporal workflows.
"""

import asyncio
from typing import List

from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.server.fastapi import APIServer
from application_sdk.server.messaging import MessageProcessorConfig

logger = get_logger(__name__)

APPLICATION_NAME = "message-processor-app"


async def process_messages_batch(messages: List[dict]):
    """Process a batch of messages.
    
    This function is called when either:
    - 25 messages have been collected (batch_size)
    - 5 seconds have passed (batch_timeout)
    
    Args:
        messages: List of messages to process
    """
    logger.info("=" * 80)
    logger.info(f"Processing batch of {len(messages)} messages")
    logger.info("=" * 80)
    
    # Count messages by type
    event_counts = {}
    
    for idx, message in enumerate(messages, 1):
        event_type = message.get("event_type", "unknown")
        event_name = message.get("event_name", "unknown")
        data = message.get("data", {})
        
        # Count event types
        key = f"{event_type}/{event_name}"
        event_counts[key] = event_counts.get(key, 0) + 1
        
    
    # Log batch summary
    logger.info("-" * 80)
    logger.info("Batch Summary:")
    logger.info(f"  Total Messages: {len(messages)}")
    logger.info(f"  Event Counts: {event_counts}")
    logger.info("=" * 80)


async def main():
    """Main entry point for the message processor application."""
    logger.info("=" * 80)
    logger.info("Starting Simple Message Processor Application")
    logger.info("=" * 80)
    
    # Initialize server without workflows (no workflow_client needed)
    server = APIServer(
        workflow_client=None,  # No Temporal workflows
        ui_enabled=True,       # Keep UI for monitoring
        has_configmap=False,   # No configmap needed
    )

    # Configure message processor (no workflows)
    # With ~5 messages/second, batch of 25 = ~5 seconds of messages
    message_config = MessageProcessorConfig(
        pubsub_component_name="messaging",
        topic="events-topic",
        batch_size=25,  # Batch mode: accumulate 25 messages
        batch_timeout=5.0,  # Or process after 5 seconds
        trigger_workflow=False,  # No Temporal workflows
    )

    # Register the message processor with custom callback
    server.register_message_processor(
        config=message_config,
        process_callback=process_messages_batch
    )

    # Start message processors
    await server.start_message_processors()

    logger.info("Configuration:")
    logger.info(f"  - Application: {APPLICATION_NAME}")
    logger.info(f"  - Message Processor: kafka-input")
    logger.info(f"  - Batch Size: {message_config.batch_size} messages")
    logger.info(f"  - Batch Timeout: {message_config.batch_timeout} seconds")
    logger.info(f"  - Expected Rate: ~5 messages/second")
    logger.info(f"  - Mode: Batch processing (no workflows)")
    logger.info("=" * 80)
    logger.info("Application ready to process messages!")
    logger.info("=" * 80)
    
    # Start server on port 3000 (configured in run.sh)
    await server.start(host="0.0.0.0", port=3000)


if __name__ == "__main__":
    asyncio.run(main())

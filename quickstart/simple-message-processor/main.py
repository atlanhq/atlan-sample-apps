"""Simple Message Processor Application.

This application demonstrates how to use the application-sdk MessageProcessor
to process messages from Kafka in batches without Temporal workflows.
"""

import asyncio
import random
import time
from typing import Any, Dict

from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.server.fastapi import APIServer
from application_sdk.server.fastapi.models import PubSubSubscription, BulkSubscribe

logger = get_logger(__name__)

APPLICATION_NAME = "message-processor-app"

# Track message counts across requests
message_counts: Dict[str, int] = {}
total_messages = 0


async def process_message(message: Dict[str, Any]):
    """Process a single CloudEvent message from Dapr pubsub.
    
    Dapr pubsub sends one CloudEvent per HTTP request.
    
    Args:
        message: CloudEvent message dict with fields like 'data', 'id', 'source', etc.
    """
    global total_messages
    total_messages += 1
    # Extract event data - Dapr wraps the actual payload in 'data' field
    event_data = message.get("data", message)
    event_type = event_data.get("event_type", "unknown")
    event_name = event_data.get("event_name", "unknown")
    
    # Count event types
    key = f"{event_type}/{event_name}"
    message_counts[key] = message_counts.get(key, 0) + 1
    
    # Log every 10 messages
    if total_messages % 10 == 0:
        logger.info("=" * 80)
        logger.info(f"Processed {total_messages} messages so far")
        logger.info(f"Event Counts: {message_counts}")
        logger.info("=" * 80)
    
    logger.info(f"Processing single message for event type: {event_type}")
    if event_type == "payment_events":
        logger.info(f"Dropping payment_events message to DLQ from single message: {event_data}")
        return {"status": "DROP"}
    elif event_type == "inventory_events":
        logger.info(f"Retrying inventory_events message from single message: {event_data}")
        # randomly retry or success
        if random.random() < 0.5:
            return {"status": "RETRY"}
        else:
            return {"status": "SUCCESS"}
    else:
        return {"status": "SUCCESS"}



async def bulk_process_message(request: Dict[str, Any]):
    """Process messages from Dapr pubsub (handles both bulk and single message formats).
    
    Dapr bulk subscribe SHOULD send:
    {"entries": [{"entryId": "...", "event": {...}}, ...]}
    
    But currently Dapr is sending individual CloudEvents:
    {"data": {...}, "id": "...", "source": "...", ...}
    
    This handler supports both formats.
    """
    global total_messages
    time.sleep(5)
    
    # Check if this is bulk format (has "entries") or single CloudEvent format
    if "entries" in request:
        # Bulk format
        entries = request.get("entries", [])
        batch_size = len(entries)
        logger.info(f"Received BULK batch of {batch_size} messages")
        statuses = []
        for entry in entries:
            total_messages += 1
            entry_id = entry.get("entryId", "unknown")
            event = entry.get("event", {})
            event_data = event.get("data", {})
            
            event_type = event_data.get("event_type", "unknown")
            event_name = event_data.get("event_name", "unknown")
            key = f"{event_type}/{event_name}"
            message_counts[key] = message_counts.get(key, 0) + 1
            
            # Return RETRY for inventory_events
            if event_type == "inventory_events":
                statuses.append({"entryId": entry_id, "status": "RETRY"})
            # Return DROP for payment_events - sends to dead letter topic
            elif event_type == "payment_events":
                logger.info(f"Dropping payment_events message to DLQ: {event_data}")
                statuses.append({"entryId": entry_id, "status": "DROP"})
            else:
                statuses.append({"entryId": entry_id, "status": "SUCCESS"})
        
        logger.info(f"Bulk processed {batch_size} messages (total: {total_messages})")
        return {"statuses": statuses}
    else:
        # Single CloudEvent format (Dapr not actually batching)
        total_messages += 1
        event_data = request.get("data", {})
        event_type = event_data.get("event_type", request.get("type", "unknown"))
        event_name = event_data.get("event_name", "unknown")
        
        key = f"{event_type}/{event_name}"
        message_counts[key] = message_counts.get(key, 0) + 1
        
        # Log every 100 messages
        if total_messages % 10 == 0:
            logger.info(f"Processed {total_messages} messages (single-mode on bulk topic)")
            logger.info(f"Event Counts: {message_counts}")
        time.sleep(2)
        
        # Return RETRY for inventory_events
        if event_type == "inventory_events":
            return {"status": "RETRY"}

        # Return DROP for payment_events - sends to dead letter topic
        if event_type == "payment_events":
            logger.info(f"Dropping payment_events message to DLQ: {event_data}")
            return {"status": "DROP"}
        return {"status": "SUCCESS"}


async def main():
    """Main entry point for the message processor application."""
    logger.info("=" * 80)
    logger.info("Starting Simple Message Processor Application")
    logger.info("=" * 80)
    
    # Initialize server without workflows (no workflow_client needed)
    # Define subscriptions with message_handler callbacks - SDK will auto-register routes
    pubsub_subscription = PubSubSubscription(
        pubsub_component_name="messaging",
        topic="events-topic",
        route="events-topic",
        dead_letter_topic="events-topic-dlq",
        message_handler=process_message,  # Callback for single messages
    )

    bulk_pubsub_subscription = PubSubSubscription(
        pubsub_component_name="messaging",
        topic="events-topic-bulk",
        route="events-topic-bulk",
        bulk_subscribe=BulkSubscribe(
            enabled=True,
            maxMessagesCount=100,
            maxAwaitDurationMs=1000,
        ),
        dead_letter_topic="events-topic-bulk-dlq",
        message_handler=bulk_process_message,  # Callback for bulk messages
    )

    # SDK automatically registers routes based on message_handler in subscriptions
    server = APIServer(
        workflow_client=None,  # No Temporal workflows
        ui_enabled=True,       # Keep UI for monitoring
        has_configmap=False,
        messaging_subscriptions=[pubsub_subscription, bulk_pubsub_subscription],
    )

    logger.info("Configuration:")
    logger.info(f"  - Application: {APPLICATION_NAME}")
    logger.info(f"  - Topic: events-topic")
    logger.info(f"  - Mode: Per-message processing (no workflows)")
    logger.info("=" * 80)
    logger.info("Application ready to process messages!")
    logger.info("=" * 80)
    
    # Start server on port 3000 (configured in run.sh)
    await server.start(host="0.0.0.0", port=3000)


if __name__ == "__main__":
    asyncio.run(main())

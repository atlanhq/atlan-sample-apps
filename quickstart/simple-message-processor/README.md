# Simple Message Processor

A lightweight Kafka message processor using the Atlan Application SDK with **PubSub subscriptions and callback handlers**.

## Features

- ✅ **PubSub Subscriptions** - Declarative subscription configuration with callback handlers
- ✅ **Bulk Subscribe** - Process messages in batches using Dapr bulk subscribe
- ✅ **Dead Letter Queue** - Automatic DLQ support for failed messages
- ✅ **No Temporal** - No workflow orchestration overhead
- ✅ **Simple** - Just define subscriptions with handler functions
- ✅ **Dapr Integration** - Uses Dapr for Kafka connectivity

## Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Start Dapr sidecar (in one terminal)
uv run poe start-dapr

# 3. Start the processor (in another terminal)
uv run poe start-processor

# 4. Publish test messages (optional, in another terminal)
uv run poe publish-messages
```

**Stop dependencies when done:**
```bash
uv run poe stop-deps
```

## Architecture

```
Kafka Topic (events-topic / events-topic-bulk)
    ↓ (Dapr PubSub)
PubSubSubscription (with message_handler callback)
    ↓
Your Handler Function
    ↓
Return Status (SUCCESS / RETRY / DROP)
```

## Usage

### Define Subscriptions with Handlers

```python
from application_sdk.server.fastapi import APIServer
from application_sdk.server.fastapi.models import PubSubSubscription, BulkSubscribe

# Handler function - receives CloudEvent message
async def process_message(message: dict):
    event_data = message.get("data", {})
    event_type = event_data.get("event_type", "unknown")
    
    if event_type == "payment_events":
        return {"status": "DROP"}  # Send to DLQ
    elif event_type == "inventory_events":
        return {"status": "RETRY"}  # Retry later
    else:
        return {"status": "SUCCESS"}  # Processed OK

# Create subscription with handler
subscription = PubSubSubscription(
    pubsub_component_name="messaging",
    topic="events-topic",
    route="events-topic",
    message_handler=process_message,  # Required callback
    dead_letter_topic="events-topic-dlq",  # Optional DLQ
)

# Start server - routes are auto-registered from subscriptions
server = APIServer(
    messaging_subscriptions=[subscription],
)
await server.start()
```

### Bulk Subscribe (Batch Processing)

```python
async def bulk_handler(request: dict):
    # Bulk format: {"entries": [{"entryId": "...", "event": {...}}, ...]}
    if "entries" in request:
        statuses = []
        for entry in request["entries"]:
            entry_id = entry.get("entryId")
            event = entry.get("event", {})
            # Process each message...
            statuses.append({"entryId": entry_id, "status": "SUCCESS"})
        return {"statuses": statuses}
    else:
        # Single message fallback
        return {"status": "SUCCESS"}

bulk_subscription = PubSubSubscription(
    pubsub_component_name="messaging",
    topic="events-topic-bulk",
    route="events-topic-bulk",
    message_handler=bulk_handler,
    bulk_subscribe=BulkSubscribe(
        enabled=True,
        maxMessagesCount=100,
        maxAwaitDurationMs=1000,
    ),
    dead_letter_topic="events-topic-bulk-dlq",
)
```

## Message Status Responses

| Status | Description |
|--------|-------------|
| `SUCCESS` | Message processed successfully |
| `RETRY` | Dapr will retry delivering the message |
| `DROP` | Message sent to dead letter topic (if configured) |

## Configuration

### PubSubSubscription Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pubsub_component_name` | str | ✅ | Dapr pubsub component name |
| `topic` | str | ✅ | Kafka topic to subscribe to |
| `route` | str | ✅ | HTTP route path for handler |
| `message_handler` | Callable | ✅ | Async function to handle messages |
| `bulk_subscribe` | BulkSubscribe | ❌ | Bulk subscribe configuration |
| `dead_letter_topic` | str | ❌ | Topic for failed messages |

### BulkSubscribe Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | False | Enable bulk subscribe |
| `maxMessagesCount` | int | 100 | Max messages per batch |
| `maxAwaitDurationMs` | int | 100 | Max wait time in ms |

## Dapr Subscriptions

The SDK automatically registers Dapr subscriptions. Check them with:

```bash
curl http://localhost:3500/dapr/subscribe | jq
```

Example response:
```json
[
  {
    "pubsubname": "messaging",
    "topic": "events-topic",
    "route": "/message-processor/events-topic",
    "deadLetterTopic": "events-topic-dlq"
  },
  {
    "pubsubname": "messaging",
    "topic": "events-topic-bulk",
    "route": "/message-processor/events-topic-bulk",
    "bulkSubscribe": {
      "enabled": true,
      "maxMessagesCount": 100,
      "maxAwaitDurationMs": 1000
    },
    "deadLetterTopic": "events-topic-bulk-dlq"
  }
]
```

## Project Structure

```
simple-message-processor/
├── components/
│   ├── messaging.yaml        # Kafka pubsub component
│   └── statestore.yaml       # State store (optional)
├── main.py                   # Application with subscriptions
├── publish_messages.py       # Message publisher utility
├── pyproject.toml            # Dependencies
└── README.md                 # This file
```

## Available Commands

```bash
# Start Dapr sidecar
uv run poe start-dapr

# Start message processor
uv run poe start-processor

# Publish test messages
uv run poe publish-messages

# Stop all processes
uv run poe stop-deps
```

## When to Use This

Use this pattern when:
- You need simple message processing with callbacks
- You want declarative subscription configuration
- You need bulk processing for high throughput
- You want automatic DLQ support
- You don't need workflow orchestration

For complex orchestration, state management, or long-running processes, use the workflow-based pattern instead.

## License

Apache-2.0

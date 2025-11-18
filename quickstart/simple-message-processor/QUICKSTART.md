# Quick Start - Simple Message Processor

Process Kafka messages in batches without Temporal workflows!

## What This Does

- **Receives** messages from Kafka at ~5 messages/second
- **Batches** them (25 messages OR 5 seconds, whichever comes first)
- **Processes** in batches with custom logic
- **No Temporal** - just simple batch processing

## Prerequisites

- Python 3.11+
- uv package manager
- Dapr CLI
- Kafka running on localhost:9092

## Quick Start

### 1. Install Dependencies

```bash
cd simple-message-processor
uv sync
```

### 2. Start the Application

```bash
./run.sh
```

This will:
- Check Kafka is running
- Start Dapr sidecar
- Start the message processor

You should see:
```
✅ You're up and running! Both Dapr and your app logs will appear here.
================================================================================
Starting Simple Message Processor Application
================================================================================
Configuration:
  - Application: simple-message-processor
  - Message Processor: kafka-input
  - Batch Size: 25 messages
  - Batch Timeout: 5.0 seconds
  - Expected Rate: ~5 messages/second
  - Mode: Batch processing (no workflows)
================================================================================
Application ready to process messages!
================================================================================
```

### 3. Publish Messages (in another terminal)

```bash
# Publish at 5 messages/second
uv run python publish_messages.py

# Or with custom rate (10 msg/sec for 60 seconds)
uv run python publish_messages.py --rate 10 --duration 60
```

You'll see:
```
Connected to Dapr: http://localhost:3500
Pubsub component: eventstore
Publishing to topic: events-topic
Rate: 5 messages/second
================================================================================
[14:30:01] ✓ Sent #1: user_events/created (id: 1)
[14:30:01] ✓ Sent #2: order_events/updated (id: 2)
[14:30:02] ✓ Sent #3: payment_events/processed (id: 3)
...
```

### 4. Watch the Processing

In the application terminal, you'll see batches being processed:

```
[INFO] app.processor - ✓ Received: user_events/created
[INFO] app.processor -   Added to batch (current: 1/25)
...
[INFO] __main__ - ================================================================================
[INFO] __main__ - Processing batch of 25 messages
[INFO] __main__ - ================================================================================
[INFO] __main__ - Message 1/25: Type=user_events, Name=created, Data={...}
[INFO] __main__ - Message 2/25: Type=order_events, Name=updated, Data={...}
...
[INFO] __main__ - Batch Summary:
[INFO] __main__ -   Total Messages: 25
[INFO] __main__ -   Event Counts: {'user_events/created': 5, 'order_events/updated': 8, ...}
[INFO] __main__ - ================================================================================
```

## Configuration

### Adjust Batch Size

Edit `main.py`:

```python
message_config = MessageProcessorConfig(
    binding_name="kafka-input",
    batch_size=50,  # Change this (1 = per-message, >1 = batch)
    batch_timeout=10.0,  # Change this
)
```

### Adjust Publishing Rate

```bash
# 10 messages per second
uv run python publish_messages.py --rate 10

# 1 message per second
uv run python publish_messages.py --rate 1
```

## Custom Processing

Edit the `process_messages_batch()` function in `main.py`:

```python
async def process_messages_batch(messages: List[dict]):
    """Your custom processing logic."""
    for message in messages:
        # Validate
        if not validate_message(message):
            continue
            
        # Transform
        transformed = transform_message(message)
        
        # Store
        await store_in_database(transformed)
        
        # Send to external API
        await send_to_api(transformed)
```

## Monitoring

### Check Processor Stats

```bash
curl http://localhost:3000/messages/v1/stats/kafka-input | jq
```

Response:
```json
{
  "is_running": true,
  "current_batch_size": 12,
  "batch_size_threshold": 25,
  "batch_timeout": 5.0,
  "is_batch_mode": true,
  "total_processed": 150,
  "total_errors": 0,
  "time_since_last_process": 2.3
}
```

### Check Dapr

```bash
dapr list
```

### View Logs

Logs are shown in the terminal where you ran `./run.sh`

## Stopping

Press `Ctrl+C` in both terminals:
- Application terminal
- Publisher terminal

## Troubleshooting

### "Kafka not running"

Start Kafka:
```bash
# Docker
docker ps | grep kafka

# Or Homebrew
brew services start kafka
```

### "Cannot connect to Dapr"

Make sure Dapr is running:
```bash
dapr list
```

If nothing is listed, the application isn't running. Check for errors in the logs.

### "No messages being processed"

1. Check if publisher is running
2. Verify topic name matches in both publisher and processor
3. Check Dapr components are loaded correctly

## What's Different From Other Examples?

- ❌ **No Temporal** - No workflow orchestration needed
- ❌ **No Activities** - Direct message processing
- ❌ **No Workflows** - Just simple batch logic
- ✅ **Simple** - Pure Python async functions
- ✅ **Fast** - No workflow overhead
- ✅ **Easy** - Just implement `process_messages_batch()`

## Architecture

```
┌─────────────┐
│   Kafka     │
│   Topic     │
└──────┬──────┘
       │
       │ (dapr pubsub)
       │
       ▼
┌─────────────────────────────┐
│ Message Publisher (Dapr)    │
│  - Publishes via Dapr HTTP  │
│  - Rate: 5 msg/sec          │
└─────────────────────────────┘

       │
       ▼
┌─────────────────────────────┐
│  Kafka Topic (events-topic) │
└──────┬──────────────────────┘
       │
       │ (dapr input binding)
       │
       ▼
┌─────────────────────────────┐
│ Simple Message Processor    │
│  ┌──────────────────────┐  │
│  │  SDK MessageProcessor│  │
│  │  - Batch: 25 msgs    │  │
│  │  - Timeout: 5 sec    │  │
│  └──────────┬───────────┘  │
│             │               │
│             ▼               │
│  ┌──────────────────────┐  │
│  │ process_messages()   │  │
│  │ - Custom logic       │  │
│  │ - No workflows       │  │
│  └──────────────────────┘  │
└─────────────────────────────┘
```

## Next Steps

1. Implement custom processing logic in `process_messages_batch()`
2. Add error handling for specific message types
3. Integrate with your database/APIs
4. Add monitoring and alerts
5. Deploy to production!

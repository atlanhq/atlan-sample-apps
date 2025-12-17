# Simple Message Processor

A lightweight Kafka message processor using the Atlan Application SDK - **no workflows, no activities, just pure message processing!**

## Features

- ✅ **Batch Processing** - Processes messages in configurable batches (25 messages or 5 seconds)
- ✅ **No Temporal** - No workflow orchestration overhead
- ✅ **Simple** - Just implement your processing function
- ✅ **Dapr Integration** - Uses Dapr for Kafka connectivity
- ✅ **Built-in Stats** - Monitor processing via HTTP endpoint

## Quick Start

```bash
# 1. Configure environment (first time only)
cp .env.example .env
# Edit .env if needed for custom Kafka/Dapr configuration

# 2. Install dependencies
uv sync

# 3. Download Dapr components (first time only)
uv run poe download-components

# 4. Start all dependencies (Kafka, Dapr, Temporal)
uv run poe start-deps

# 5. Start the processor (in another terminal)
./run.sh

# 6. Publish test messages (optional, in another terminal)
uv run poe publish-messages
```

**Stop dependencies when done:**
```bash
uv run poe stop-deps
```

## Configuration

This application uses a `.env` file for configuration. See [ENV_CONFIG.md](ENV_CONFIG.md) for detailed documentation on all available configuration options.

**Quick configuration:**
```bash
# Kafka settings
KAFKA_HOST=localhost
KAFKA_PORT=9092
KAFKA_TOPIC=events-topic

# Dapr settings
DAPR_HTTP_PORT=3500
APP_PORT=3000
```

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

## Architecture

```
Kafka Topic
    ↓ (Dapr Input Binding)
Message Processor
    ↓ (Batch: 25 msgs OR 5 sec)
process_messages_batch()
    ↓ (Your Custom Logic)
Done!
```

No workflows. No activities. Just messages in → processing → done.

## Configuration

Edit `main.py` to customize:

```python
message_config = MessageProcessorConfig(
    binding_name="kafka-input",
    batch_size=25,        # Change batch size
    batch_timeout=5.0,    # Change timeout
    trigger_workflow=False,  # No workflows
)
```

## Monitoring

```bash
# Check stats
curl http://localhost:3000/messages/v1/stats/kafka-input | jq

# Check Dapr
dapr list
```

## Custom Processing

Edit the `process_messages_batch()` function in `main.py`:

```python
async def process_messages_batch(messages: List[dict]):
    """Your custom processing logic here."""
    for message in messages:
        # Validate
        # Transform  
        # Store
        # Send to API
        # etc.
```

## What's Different?

Unlike other examples with Temporal workflows:
- ❌ No `workflow.py`
- ❌ No `activities.py`
- ❌ No Temporal server required
- ✅ Just a simple async function
- ✅ Much simpler to understand and debug
- ✅ Perfect for straightforward message processing

## When to Use This

Use this pattern when:
- You need simple message processing
- You don't need workflow orchestration
- You want low overhead
- You want to process in batches

For complex orchestration, state management, or long-running processes, use the workflow-based pattern instead.

## Project Structure

```
simple-message-processor/
├── app/
│   └── __init__.py           # Empty - no workflow/activities
├── components/
│   ├── kafka-input-binding.yaml  # Kafka input
│   └── eventstore.yaml           # Kafka pubsub (for publisher)
├── main.py                   # Application entry point
├── publish_messages.py       # Message publisher utility
├── run.sh                    # Startup script
├── pyproject.toml            # Dependencies (no workflows)
├── README.md                 # This file
└── QUICKSTART.md             # Detailed guide
```

## Available Commands

### Setup
```bash
# Download Dapr components (run once, or when updating)
uv run poe download-components
```

### Dependency Management
```bash
# Start all dependencies (Kafka, Dapr, Temporal)
uv run poe start-deps

# Stop all dependencies
uv run poe stop-deps
```

### Running the Application
```bash
# Start the message processor (requires dependencies to be running)
./run.sh
# or
uv run poe start-processor
```

### Publishing Messages
```bash
# Publish messages for 10 seconds at 5 msg/sec
uv run poe publish-messages

# Publish continuously
uv run python publish_messages.py

# Publish with custom rate (10 msg/sec for 30 seconds)
uv run python publish_messages.py --rate 10 --duration 30
```

## License

Apache-2.0

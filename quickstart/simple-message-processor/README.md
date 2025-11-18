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
# 1. Install dependencies
uv sync

# 2. Start the processor
./run.sh

# 3. Publish messages (in another terminal)
uv run python publish_messages.py
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

## License

Apache-2.0

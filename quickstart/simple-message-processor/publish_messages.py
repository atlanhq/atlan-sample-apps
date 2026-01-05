#!/usr/bin/env python3
"""Continuous Message Publisher using Dapr.

This utility continuously publishes messages to Kafka via Dapr pubsub
at a rate of ~5 messages/second.
"""

import argparse
import asyncio
import json
import os
import random
from datetime import datetime
from typing import Optional
from dapr.clients import DaprClient

import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DaprMessagePublisher:
    """Publishes messages to Kafka via Dapr pubsub."""

    def __init__(
        self,
        dapr_http_port: int = 3500,
        pubsub_name: str = "messaging",
        topic: str = "events-topic",
        rate: int = 5,
    ):
        """Initialize the message publisher.

        Args:
            dapr_http_port: Dapr HTTP port
            pubsub_name: Dapr pubsub component name
            topic: Topic to publish to
            rate: Messages per second
        """
        self.dapr_url = f"http://localhost:{dapr_http_port}"
        self.pubsub_name = pubsub_name
        self.topic = topic
        self.rate = rate
        self.message_count = 0
        self.error_count = 0

        # Event types and names for variety
        self.event_types = [
            "user_events",
            "order_events",
            "payment_events",
            "inventory_events",
            "notification_events",
        ]
        self.event_names = ["created", "updated", "deleted", "processed", "failed"]

        print(f"Dapr HTTP endpoint: {self.dapr_url}")
        print(f"Pubsub component: {self.pubsub_name}")
        print(f"Publishing to topic: {self.topic}")
        print(f"Rate: {self.rate} messages/second")
        print("=" * 80)

    def generate_message(self) -> dict:
        """Generate a random message.

        Returns:
            dict: Message with event_type, event_name, data, and metadata
        """
        event_type = random.choice(self.event_types)
        event_name = random.choice(self.event_names)

        return {
            "event_type": event_type,
            "event_name": event_name,
            "data": {
                "id": self.message_count + 1,
                "message": f"Message {self.message_count + 1}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "random_value": random.randint(1, 10000),
                "user_id": random.randint(1, 1000),
                "amount": round(random.uniform(10.0, 1000.0), 2),
            },
            "metadata": {
                "source": "dapr_message_publisher",
                "publisher_id": "simple-message-processor-publisher",
                "sequence": self.message_count + 1,
            },
        }

    async def publish_message_with_dapr_client(self, message: dict) -> bool:
        try:
            with DaprClient() as client:
                client.publish_event(
                    pubsub_name=self.pubsub_name,
                    topic_name=self.topic,
                    data=json.dumps(message),
                    data_content_type="application/json",
                )
                client.publish_event(
                    pubsub_name=self.pubsub_name,
                    topic_name=self.topic + "-bulk",
                    data=json.dumps(message),
                    data_content_type="application/json",
                )
                self.message_count += 1
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"✓ Sent #{self.message_count}: "
                    f"{message['event_type']}/{message['event_name']} "
                    f"(id: {message['data']['id']})"
                )
                return True
        except Exception as e:
            self.error_count += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Error publishing message: {e}")
            return False

    async def run(self, duration: Optional[int] = None):
        """Run the message publisher.

        Args:
            duration: Duration in seconds (None = run indefinitely)
        """
        start_time = asyncio.get_event_loop().time()
        sleep_time = 1.0 / self.rate  # Time between messages

        print("Starting message publisher...")
        print(f"Press Ctrl+C to stop")
        print("=" * 80)

        try:
            while True:
                # Check duration
                if duration:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= duration:
                        print(f"\nDuration of {duration}s reached, stopping...")
                        break

                # Generate and publish message
                message = self.generate_message()
                await self.publish_message_with_dapr_client(message)

                # Sleep to maintain rate
                await asyncio.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n\nReceived interrupt signal, stopping...")

        finally:
            await self.shutdown()

    async def shutdown(self):
        """Shutdown the publisher and print statistics."""
        print("=" * 80)
        print("Shutting down publisher...")
        print(f"Published {self.message_count} messages")
        print(f"Errors: {self.error_count}")
        if self.message_count > 0:
            success_rate = (
                (self.message_count / (self.message_count + self.error_count)) * 100
            )
            print(f"Success rate: {success_rate:.1f}%")
        print("Publisher stopped")


async def main():
    """Main entry point."""
    # Get defaults from environment variables
    default_dapr_port = int(os.getenv("DAPR_HTTP_PORT", "3500"))
    
    parser = argparse.ArgumentParser(
        description="Publish messages to Kafka via Dapr pubsub"
    )
    parser.add_argument(
        "--dapr-http-port",
        type=int,
        default=default_dapr_port,
        help=f"Dapr HTTP port (default: {default_dapr_port} from env)",
    )
    parser.add_argument(
        "--pubsub-name",
        default="messaging",
        help="Dapr pubsub component name (default: messaging)",
    )
    parser.add_argument(
        "--topic",
        default="events-topic",
        help="Topic to publish to (default: events-topic)",
    )
    parser.add_argument(
        "--rate",
        type=int,
        default=5,
        help="Messages per second (default: 5)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Duration in seconds (default: run indefinitely)",
    )

    args = parser.parse_args()

    # Check if Dapr is accessible
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:{args.dapr_http_port}/v1.0/healthz", timeout=2.0
            )
            if response.status_code != 204:
                print(
                    f"WARNING: Dapr health check returned status {response.status_code}"
                )
    except Exception as e:
        print(f"ERROR: Cannot connect to Dapr on port {args.dapr_http_port}")
        print(f"Make sure Dapr is running: dapr list")
        print(f"Error: {e}")
        return

    publisher = DaprMessagePublisher(
        dapr_http_port=args.dapr_http_port,
        pubsub_name=args.pubsub_name,
        topic=args.topic,
        rate=args.rate,
    )

    await publisher.run(duration=args.duration)


if __name__ == "__main__":
    asyncio.run(main())

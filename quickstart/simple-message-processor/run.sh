#!/bin/bash

# Run Simple Message Processor

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=== Simple Message Processor ===${NC}"
echo ""

# Check if Kafka is running
if ! nc -z localhost 9092 2>/dev/null; then
    echo -e "${RED}Error: Kafka not running on localhost:9092${NC}"
    echo "Please start Kafka first"
    exit 1
fi
echo -e "${GREEN}✓ Kafka is running${NC}"

# Check if components directory has required files
if [ ! -f "components/kafka-input-binding.yaml" ]; then
    echo -e "${RED}Error: Kafka input binding configuration not found${NC}"
    exit 1
fi

# Copy additional Dapr components from application-sdk if needed
SDK_COMPONENTS="../../../application-sdk/components"
if [ -d "$SDK_COMPONENTS" ]; then
    echo -e "${YELLOW}Copying Dapr components from SDK...${NC}"
    cp -n $SDK_COMPONENTS/*.yaml components/ 2>/dev/null || true
    echo -e "${GREEN}✓ Components ready${NC}"
fi

echo ""
echo -e "${BLUE}Starting application with Dapr (no Temporal)...${NC}"
echo ""

# Run with Dapr (no Temporal needed)
dapr run \
  --app-id simple-message-processor \
  --app-port 3000 \
  --dapr-http-port 3500 \
  --dapr-grpc-port 50001 \
  --resources-path ./components \
  --log-level info \
  -- uv run python main.py

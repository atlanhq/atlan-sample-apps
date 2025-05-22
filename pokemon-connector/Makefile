# Define variables
APP_NAME := phoenix-hello-world-app

# Phony targets
.PHONY: install start-deps run

# Attempt to include .env file if it exists
-include .env

# Default values (will be used if .env doesn't exist or variables are not set)
ATLAN_APP_HTTP_HOST ?= 0.0.0.0
ATLAN_APP_HTTP_PORT ?= 8000
ATLAN_APP_DASHBOARD_HTTP_HOST ?= 0.0.0.0
ATLAN_APP_DASHBOARD_HTTP_PORT ?= 8050
ATLAN_DAPR_APP_PORT ?= 3000
ATLAN_DAPR_HTTP_PORT ?= 3500
ATLAN_DAPR_GRPC_PORT ?= 50001
ATLAN_TEMPORAL_HOST ?= 127.0.0.1
ATLAN_TEMPORAL_PORT ?= 7233
ATLAN_TEMPORAL_UI_ENABLED ?= true
ATLAN_TEMPORAL_UI_HOST ?= 127.0.0.1
ATLAN_TEMPORAL_UI_PORT ?= 8233
ATLAN_TEMPORAL_METRICS_PORT ?= 8234

# Run Temporal locally
start-temporal-dev:
	@if [ "$(ATLAN_TEMPORAL_UI_ENABLED)" = true ]; then \
		temporal server start-dev --ip $(ATLAN_TEMPORAL_HOST) --port $(ATLAN_TEMPORAL_PORT) --ui-ip $(ATLAN_TEMPORAL_UI_HOST) --ui-port $(ATLAN_TEMPORAL_UI_PORT) --metrics-port $(ATLAN_TEMPORAL_METRICS_PORT); \
	else \
		temporal server start-dev --ip $(ATLAN_TEMPORAL_HOST) --port $(ATLAN_TEMPORAL_PORT) --metrics-port $(ATLAN_TEMPORAL_METRICS_PORT) --headless; \
	fi

start-dapr:
	dapr run --app-id app --app-port $(ATLAN_DAPR_APP_PORT) --dapr-http-port $(ATLAN_DAPR_HTTP_PORT) --dapr-grpc-port $(ATLAN_DAPR_GRPC_PORT) --dapr-http-max-request-size 1024 --resources-path .venv/src/application-sdk/components

start-deps:
	@echo "Starting all services in detached mode..."
	make start-dapr &
	make start-temporal-dev &
	@echo "Services started. Proceeding..."

install:
	# Configure git to use https instead of ssh or git
	@if git ls-remote git@github.com:atlanhq/application-sdk.git > /dev/null 2>&1; then \
		echo "Git is configured to use SSH Protocol"; \
	elif git ls-remote https://github.com/atlanhq/application-sdk.git > /dev/null 2>&1; then \
		echo "Git is configured to use HTTPS Protocol. Configuring to use HTTPS instead..."; \
		git config --global url."https://github.com/".insteadOf "git@github.com:"; \
	else \
		echo "Git is not configured to use SSH or Git Protocol. Please configure Git to use SSH or Git Protocol."; \
		exit 1; \
	fi
	# Configure poetry to use project-specific virtualenv
	poetry config virtualenvs.in-project true

	# Install the dependencies
	poetry install -vvv
	poetry update application-sdk --dry-run

# Run the application
run-app:
	ATLAN_APP_HTTP_HOST=$(ATLAN_APP_HTTP_HOST) \
	ATLAN_APP_HTTP_PORT=$(ATLAN_APP_HTTP_PORT) \
	ATLAN_APP_DASHBOARD_HTTP_HOST=$(ATLAN_APP_DASHBOARD_HTTP_HOST) \
	ATLAN_APP_DASHBOARD_HTTP_PORT=$(ATLAN_APP_DASHBOARD_HTTP_PORT) \
	OTEL_EXPORTER_OTLP_ENDPOINT="http://$(ATLAN_APP_HTTP_HOST):$(ATLAN_APP_HTTP_PORT)/telemetry" \
	OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf" \
	OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true \
	OTEL_PYTHON_EXCLUDED_URLS="/telemetry/.*,/system/.*" \
	poetry run ./.venv/bin/opentelemetry-instrument --traces_exporter otlp --metrics_exporter otlp --logs_exporter otlp --service_name hello-world-application python main.py

run-dashboard:
	PYTHONPATH=./.venv/src/application-sdk/ \
	ATLAN_APP_DASHBOARD_HTTP_HOST=$(ATLAN_APP_DASHBOARD_HTTP_HOST) \
	ATLAN_APP_DASHBOARD_HTTP_PORT=$(ATLAN_APP_DASHBOARD_HTTP_PORT) \
	poetry run python .venv/src/application-sdk/dashboard/app.py

run-dev:
	$(MAKE) stop-all && $(MAKE) start-deps && sleep 5 && $(MAKE) run-app

run:
	$(MAKE) run-app

stop-all:
	@echo "Stopping all detached processes..."
	@pkill -f "temporal server start-dev" || true
	@pkill -f "dapr run --app-id app" || true
	@pkill -f "python main.py" || true        # For run-app
	@pkill -f "python .venv/src/application-sdk/dashboard/app.py" || true  # For run-dashboard
	@echo "All detached processes stopped."

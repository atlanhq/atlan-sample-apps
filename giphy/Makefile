
# Define variables
APP_NAME := sample-apps

# Phony targets
.PHONY: run start-dapr start-temporal-dev start-all

# Run Temporal locally
start-temporal-dev:
	temporal server start-dev --db-filename /tmp/temporal.db

# Run Dapr locally
start-dapr:
	dapr run --enable-api-logging --log-level debug --app-id app --app-port 3000 --dapr-http-port 3500 --dapr-grpc-port 50001 --dapr-http-max-request-size 1024 --resources-path components

# Start all services in detached mode
start-deps:
	@echo "Starting all services in detached mode..."
	make start-dapr &
	make start-temporal-dev &
	@echo "Services started. Proceeding..."

# Install dependencies
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
	poetry config experimental.system-git-client true

	# Install the dependencies
	poetry install -vv
	poetry update application-sdk --dry-run



# Stop all services
stop-all:
	@echo "Stopping all detached processes..."
	@pkill -f "temporal server start-dev" || true
	@pkill -f "dapr run --app-id app" || true
	@echo "All detached processes stopped."


# Run the application
run:
	POETRY_PLUGIN_DOTENV_LOCATION=".env" \
	poetry run python main.py

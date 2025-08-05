
# App Docker Installation

## Files Overview
- **Dockerfile**: Defines the container image with Python dependencies and application setup
- **supervisord.conf**: Configures process management to run multiple services within the container
- **entrypoint.sh**: Initializes the container environment and starts the application services

## Build and Run

### Build the Docker image:

**Important: Run from the app's root directory**

You must be in the app's root directory (where `main.py` is located), not in the `deploy/` folder, as Docker needs the full app context for building.
```bash
docker build --no-cache -f ./deploy/Dockerfile -t app:latest .
```

### Run the Docker container:

**If your Temporal service is running on the host machine:**
```bash
docker run -p 8000:8000 --add-host=host.docker.internal:host-gateway -e ATLAN_WORKFLOW_HOST=host.docker.internal -e ATLAN_WORKFLOW_PORT=7233 --user 1000:1000 app
```

**If your Temporal service is running elsewhere (remote server/container):**
```bash
docker run -p 8000:8000 -e ATLAN_WORKFLOW_HOST=<your-temporal-host> -e ATLAN_WORKFLOW_PORT=<your-temporal-port> --user 1000:1000 app
```
*Replace `<your-temporal-host>` and `<your-temporal-port>` with your actual Temporal service hostname/IP and port.*

# 📨 Events App

A simple application demonstrating how to build apps with the Atlan Application SDK using events.

<img width="1505" alt="Screenshot 2025-06-18 at 1 42 09 PM" src="https://github.com/user-attachments/assets/e6bffb58-b305-4212-963c-d29d495c795b" />

## Features
- Simulates event-driven workflows
- Real-time workflow status tracking
- Integration with Temporal for workflow management
- Demonstrates async and sync activities in a workflow
- Example of basic workflow implementation

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [Dapr CLI](https://docs.dapr.io/getting-started/install-dapr-cli/)
- [Temporal CLI](https://docs.temporal.io/cli)
- Atlan instance access and API key

### Installation Guides
- [macOS Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/MAC.md)
- [Linux Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/LINUX.md)
- [Windows Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/WINDOWS.md)

## Quick Start

1. **Download required components:**
   ```bash
   uv run poe download-components
   ```

2. **Set up environment variables (see below)**

3. **Start dependencies (in separate terminal):**
   ```bash
   uv run poe start-deps
   ```

4. **Run the application:**
   ```bash
   uv run main.py
   ```

### Access the Application

Once the application is running:

- **Temporal UI**: Access the Temporal Web UI at `http://localhost:8233` (or your Temporal UI address) to monitor workflow executions.
- **Frontend**: Access the Frontend UI at `http://localhost:8000`

To see the events flow - 
1. Click "Start Workflow" on the frontend UI at `http://localhost:8000`
2. Go to the temporal dashboard to see that a new workflow of the type `WorkflowTriggeredByUI` has started
3. Wait for this workflow to finish, once finished, a new workflow will be triggered by the `workflow_end` event of this workflow of type `WorkflowTriggeredByEvent`

![swimlanes-028e52a813253d7f59311fe0fb8b4af1](https://github.com/user-attachments/assets/3eb43edb-0b5a-4f0a-99e9-baab9ef111e1)

## Development

### Project Structure
```
.
├── activities.py            # Workflow activities
├── main.py                  # Application entry point
├── workflows.py             # Workflow definitions
├── subscriber_manifest.json # Subscriber manifest
└── README.md                # This file
```

## Learning Resources
- [Temporal Documentation](https://docs.temporal.io/)
- [Atlan Application SDK Documentation](https://github.com/atlanhq/application-sdk/tree/main/docs)
- [Python FastAPI Documentation](https://fastapi.tiangolo.com/)

## Contributing
We welcome contributions! Please feel free to submit a Pull Request.

# 📨 Events App

A simple application demonstrating how to build apps with the Atlan Application SDK using events.

![Screenshot](https://github.com/user-attachments/assets/416be4d4-e137-42c4-9537-869df2c8f87e)

## Features
- Simulates event-driven workflows
- Real-time workflow status tracking
- Integration with Temporal for workflow management
- Demonstrates async and sync activities in a workflow
- Example of basic workflow implementation

## Usage

> [!NOTE]
> To run, first see the [main project README](../README.md) for prerequisites.

### Run the Events Application

```bash
uv run main.py
```

### Access the Application

Once the application is running:

- **Temporal UI**: Access the Temporal Web UI at `http://localhost:8233` (or your Temporal UI address) to monitor workflow executions.

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
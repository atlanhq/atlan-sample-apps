# 👋 Hello World

A simple starter application demonstrating how to build apps with Application SDK.

![Screenshot](https://github.com/user-attachments/assets/416be4d4-e137-42c4-9537-869df2c8f87e)

## Features
- Simple web interface to input your name
- Real-time workflow status tracking
- Integration with Temporal for workflow management
- Example of basic workflow implementation

## Usage

> [!NOTE]
> To run, first see [README.md](../README.md) for prerequisites.

### Run the Hello World Application

```bash
uv run main.py
```

### Access the Application

Once the application is running:

-   **Web Interface**: Open your browser and go to `http://localhost:8000` (or the port configured for `APP_HTTP_PORT`).
-   **Temporal UI**: Access the Temporal Web UI at `http://localhost:8233` (or your Temporal UI address) to monitor workflow executions.

## Development

### Project Structure
```
hello_world/
├── frontend/           # Frontend assets
│   ├── static/        # Static files (CSS, JS)
│   └── templates/     # HTML templates
├── activities.py       # Workflow activities
├── workflow.py        # Workflow definitions
└── main.py            # Application entry point
```

## Learning Resources
- [Temporal Documentation](https://docs.temporal.io/)
- [Atlan Application SDK Documentation](https://github.com/atlanhq/application-sdk/tree/main/docs)
- [Python FastAPI Documentation](https://fastapi.tiangolo.com/)

## Contributing
We welcome contributions! Please feel free to submit a Pull Request.
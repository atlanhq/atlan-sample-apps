# 👋 Hello World

A simple starter application demonstrating how to build apps with Application SDK.

![Screenshot](https://github.com/user-attachments/assets/416be4d4-e137-42c4-9537-869df2c8f87e)

## Features
- Simple web interface to input your name
- Real-time workflow status tracking
- Integration with Temporal for workflow management
- Example of basic workflow implementation

## Usage

### Setting up your environment

1. Follow the setup instructions for your platform:
   - [Windows](https://github.com/atlanhq/application-sdk/docs/docs/setup/WINDOWS.md)
   - [Mac](https://github.com/atlanhq/application-sdk/docs/docs/setup/MAC.md)
   - [Linux](https://github.com/atlanhq/application-sdk/docs/docs/setup/LINUX.md)

### Installation

1. Clone this repository:
```bash
git clone https://github.com/atlanhq/atlan-sample-apps.git
cd hello_world
```

2. Install dependencies:
```bash
uv sync
```

This will:
- Configure git to use HTTPS
- Set up uv with project-specific virtualenv
- Install all dependencies

## Running the Application

### Start Dependencies
Start Temporal and Dapr services:
```bash
uv run poe start-deps
```

### Run the Application
Start the application:
```bash
uv run main.py
```

### Access the Application
Once running, access the application at:
- Web Interface: `http://localhost:8000`
- Temporal UI: `http://localhost:8233`

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
# 🤡 Giphy

An app that sends gifs to your friends via email. Built with Application SDK.

https://github.com/user-attachments/assets/f89fc296-d442-4317-91a5-4a7c8b28def6

## Features

- Search and send GIFs to multiple recipients
- Real-time workflow status tracking
- Support for multiple email recipients
- Integration with Temporal for workflow management
- Integration with Giphy API and SendGrid

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
cd giphy
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
giphy/
├── frontend/           # Frontend assets
│   ├── static/        # Static files (CSS, JS)
│   └── templates/     # HTML templates
├── activities.py       # Workflow activities
├── workflow.py        # Workflow definitions
└── main.py            # Application entry point
```

> [!NOTE]
> Make sure you have a `.env` file that matches the [.env.example](.env.example) file in this directory.


## Learning Resources

- [Temporal Documentation](https://docs.temporal.io/)
- [Atlan Application SDK Documentation](https://github.com/atlanhq/application-sdk/tree/main/docs)
- [Python FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Giphy API Documentation](https://developers.giphy.com/docs/api)
- [SendGrid Documentation](https://docs.sendgrid.com/)

## Contributing

We welcome contributions! Please feel free to submit a Pull Request.

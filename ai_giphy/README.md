# 🤖 AI Giphy Messenger

An intelligent application that uses an AI agent to fetch relevant GIFs based on your descriptions and sends them to your friends via email. Built with the Application SDK, Langchain, and Temporal.

https://github.com/user-attachments/assets/fd23ce3b-d63d-480d-a4fe-4258fc5de5c7

## Features

- **AI-Powered GIF Selection**: Describe the GIF you want (e.g., "a happy cat dancing") and the AI agent will find a suitable one.
- **Automated Emailing**: Automatically sends the selected GIF to specified recipients.
- **Workflow Management**: Leverages Temporal for robust workflow orchestration.
- **Extensible Agent**: Utilizes Langchain for building the AI agent, allowing for easy extension of its capabilities.
- **Clear UI**: Simple web interface to interact with the AI agent.

## Usage

> [!NOTE]
> To run, first see [README.md](../README.md) for prerequisites.


### Environment Variables

Create a `.env` file in the `ai_giphy` root directory and populate it with the following variables. Obtain the necessary API keys from their respective services.

```env
# Giphy API Key
GIPHY_API_KEY=your_giphy_api_key

# SMTP Configuration (e.g., SendGrid)
SMTP_HOST=your_smtp_host (e.g., smtp.sendgrid.net)
SMTP_PORT=your_smtp_port (e.g., 587)
SMTP_USERNAME=your_smtp_username (e.g., apikey for SendGrid)
SMTP_PASSWORD=your_smtp_password_or_api_key
SMTP_SENDER=your_sender_email (e.g., support@yourdomain.com)

# Azure OpenAI Configuration (used by the AI agent)
APP_AZURE_OPENAI_API_KEY=your_azure_openai_api_key
APP_AZURE_OPENAI_API_VERSION=your_azure_openai_api_version
APP_AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
APP_AZURE_OPENAI_DEPLOYMENT_NAME=your_azure_openai_deployment_name

```

### Run the AI Giphy Application

```bash
uv run main.py
```
This will start the Temporal worker and the FastAPI web server.

### Access the Application

Once the application is running:

-   **Web Interface**: Open your browser and go to `http://localhost:8000` (or the port configured for `APP_HTTP_PORT`).
-   **Temporal UI**: Access the Temporal Web UI at `http://localhost:8233` (or your Temporal UI address) to monitor workflow executions.

## Development

### Project Structure

```
ai_giphy/
├── .venv/              # Virtual environment (created by uv)
├── frontend/           # Frontend assets
│   ├── static/         # Static files (CSS, JS - if any)
│   └── templates/      # HTML templates (e.g., index.html)
├── activities.py       # Temporal activities (e.g., running the AI agent)
├── ai_agent.py         # Core logic for the AI agent (Langchain tools, LLM interaction)
├── workflow.py         # Temporal workflow definition
├── main.py             # Application entry point (FastAPI server, Temporal worker setup)
├── pyproject.toml      # Project metadata and dependencies for uv
├── uv.lock         # Exact versions of dependencies
├── Makefile            # Make commands for common tasks
├── .env                # Environment variables (create this file)
└── README.md           # This file
```

> [!NOTE]
> Make sure you have a `.env` file that matches the [.env.example](.env.example) file in this directory.

## Learning Resources

-   [Temporal Documentation](https://docs.temporal.io/)
-   [Atlan Application SDK Documentation](https://github.com/atlanhq/application-sdk/tree/main/docs) (Refer to the SDK version you are using)
-   [Langchain Python Documentation](https://python.langchain.com/)
-   [FastAPI Documentation](https://fastapi.tiangolo.com/)
-   [Giphy API Documentation](https://developers.giphy.com/docs/api)

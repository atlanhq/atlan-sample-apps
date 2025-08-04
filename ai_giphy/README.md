# 🤖 AI Giphy Messenger

An intelligent application that uses an AI agent to fetch relevant GIFs based on your descriptions and sends them to your friends via email. Built with the Application SDK, Langchain, and Temporal.

https://github.com/user-attachments/assets/fd23ce3b-d63d-480d-a4fe-4258fc5de5c7

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [Dapr CLI](https://docs.dapr.io/getting-started/install-dapr-cli/)
- [Temporal CLI](https://docs.temporal.io/cli)
- Giphy API key
- SMTP credentials (e.g., SendGrid)
- Azure OpenAI API credentials

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

**Access the application:**
- **Web Interface**: http://localhost:8000
- **Temporal UI**: http://localhost:8233

## Features

- **AI-Powered GIF Selection**: Describe the GIF you want (e.g., "a happy cat dancing") and the AI agent will find a suitable one.
- **Automated Emailing**: Automatically sends the selected GIF to specified recipients.
- **Workflow Management**: Leverages Temporal for robust workflow orchestration.
- **Extensible Agent**: Utilizes Langchain for building the AI agent, allowing for easy extension of its capabilities.
- **Clear UI**: Simple web interface to interact with the AI agent.


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

## Development

### Stop Dependencies
```bash
uv run poe stop-deps
```

### Run Tests
```bash
uv run pytest
```

### Project Structure

```
ai_giphy/
├── app/                # Core application logic
│   ├── activities.py   # Temporal activities (AI agent execution)
│   ├── ai_agent.py     # Core AI agent logic (Langchain tools, LLM interaction)
│   └── workflow.py     # Temporal workflow definition
├── frontend/           # Frontend assets
│   ├── static/         # Static files (CSS, JS)
│   └── templates/      # HTML templates
├── local/              # Local data storage
├── main.py             # Application entry point
├── pyproject.toml      # Dependencies and config
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

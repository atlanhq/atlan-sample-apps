# 🤖 AI Giphy Messenger

An intelligent application that uses an AI agent to fetch relevant GIFs based on your descriptions and sends them to your friends via email. Built with the Application SDK, Langchain, and Temporal.

## Features

- **AI-Powered GIF Selection**: Describe the GIF you want (e.g., "a happy cat dancing") and the AI agent will find a suitable one.
- **Automated Emailing**: Automatically sends the selected GIF to specified recipients.
- **Workflow Management**: Leverages Temporal for robust workflow orchestration.
- **Extensible Agent**: Utilizes Langchain for building the AI agent, allowing for easy extension of its capabilities.
- **Clear UI**: Simple web interface to interact with the AI agent.

## Usage

### Setting up your environment

1.  Ensure you have Python 3.10+ and Poetry installed.
2.  Follow the general setup instructions for the Application SDK for your platform:
    *   [Windows](https://github.com/atlanhq/application-sdk/blob/main/docs/setup/WINDOWS.md)
    *   [Mac](https://github.com/atlanhq/application-sdk/blob/main/docs/setup/MAC.md)
    *   [Linux](https://github.com/atlanhq/application-sdk/blob/main/docs/setup/LINUX.md)
    *   (Ensure Dapr and Temporal development server can be started)

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

### Installation

1.  Navigate to the `ai_giphy` directory:
    ```bash
    cd path/to/your/atlan-sample-apps/ai_giphy
    ```

2.  Install dependencies using Make:
    ```bash
    make install
    ```
    This command typically:
    - Configures git to use HTTPS (if applicable).
    - Sets up Poetry to create a virtual environment within the project directory.
    - Installs all Python dependencies specified in `pyproject.toml`.

## Running the Application

### 1. Start Dependencies

Ensure your Temporal development server and Dapr sidecar are running. The Application SDK often provides a way to start these:
```bash
make start-deps
```
(If this command is not available or doesn't work in your setup, you'll need to start Temporal and Dapr manually according to their documentation.)

### 2. Run the Application

1.  Activate the virtual environment (if not already active):
    ```bash
    source .venv/bin/activate
    # For Windows: .venv\Scripts\activate
    ```

2.  Start the AI Giphy application:
    ```bash
    make run
    ```
    This will start the Temporal worker and the FastAPI web server.

### 3. Access the Application

Once the application is running:

-   **Web Interface**: Open your browser and go to `http://localhost:8000` (or the port configured for `APP_HTTP_PORT`).
-   **Temporal UI**: Access the Temporal Web UI at `http://localhost:8233` (or your Temporal UI address) to monitor workflow executions.

## Development

### Project Structure

```
ai_giphy/
├── .venv/              # Virtual environment (created by Poetry)
├── frontend/           # Frontend assets
│   ├── static/         # Static files (CSS, JS - if any)
│   └── templates/      # HTML templates (e.g., index.html)
├── activities.py       # Temporal activities (e.g., running the AI agent)
├── ai_agent.py         # Core logic for the AI agent (Langchain tools, LLM interaction)
├── workflow.py         # Temporal workflow definition
├── main.py             # Application entry point (FastAPI server, Temporal worker setup)
├── pyproject.toml      # Project metadata and dependencies for Poetry
├── poetry.lock         # Exact versions of dependencies
├── Makefile            # Make commands for common tasks
├── .env                # Environment variables (create this file)
└── README.md           # This file
```

### Available Make Commands

(These are common commands; adapt if your `Makefile` differs)
-   `make install`: Sets up the development environment and installs dependencies.
-   `make start-deps`: Starts essential services like Temporal and Dapr.
-   `make run`: Runs the main application (worker and server).
-   `make stop-all`: Stops all running services (application, Temporal, Dapr).
-   `make lint`: Runs linters to check code quality.
-   `make format`: Formats the code according to defined styles.

## Learning Resources

-   [Temporal Documentation](https://docs.temporal.io/)
-   [Atlan Application SDK Documentation](https://github.com/atlanhq/application-sdk/tree/main/docs) (Refer to the SDK version you are using)
-   [Langchain Python Documentation](https://python.langchain.com/)
-   [FastAPI Documentation](https://fastapi.tiangolo.com/)
-   [Giphy API Documentation](https://developers.giphy.com/docs/api)

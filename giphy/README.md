# 🤡 Giphy

An app that sends gifs to your friends via email. Built with Application SDK.

https://github.com/user-attachments/assets/f89fc296-d442-4317-91a5-4a7c8b28def6

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [Dapr CLI](https://docs.dapr.io/getting-started/install-dapr-cli/)
- [Temporal CLI](https://docs.temporal.io/cli)
- Giphy API key
- SMTP credentials (e.g., SendGrid)

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

## Features

- Search and send GIFs to multiple recipients
- Real-time workflow status tracking
- Support for multiple email recipients
- Integration with Temporal for workflow management
- Integration with Giphy API and SendGrid

## Environment Variables

Create a `.env` file in the `giphy` root directory and populate it with the following variables. Obtain the necessary API keys from their respective services.

```env
# Giphy API Key
GIPHY_API_KEY=your_giphy_api_key

# SMTP Configuration
SMTP_HOST=your_smtp_host (e.g., smtp.sendgrid.net)
SMTP_PORT=your_smtp_port (e.g., 587)
SMTP_USERNAME=your_smtp_username (e.g., apikey for SendGrid)
SMTP_PASSWORD=your_smtp_password_or_api_key
SMTP_SENDER=your_sender_email (e.g., support@yourdomain.com)
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
giphy/
├── components/         # Dapr components (auto-downloaded)
├── frontend/           # Frontend assets
│   ├── static/        # Static files (CSS, JS)
│   └── templates/     # HTML templates
├── activities.py       # Workflow activities
├── workflow.py        # Workflow definitions
├── main.py            # Application entry point
├── pyproject.toml     # Dependencies and config
└── README.md          # This file
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

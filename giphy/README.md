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

> [!NOTE]
> To run, first see [README.md](../README.md) for prerequisites.

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

### Run the Application

Start the application:

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

# 🤡 Giphy

An app that sends gifs to your friends via email. Built with Application SDK.

![Demo](https://github.com/user-attachments/assets/f89fc296-d442-4317-91a5-4a7c8b28def6)

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

### Environment Variables
Update the `.env` file in the root directory with the following variables:

```env
GIPHY_API_KEY=your_giphy_api_key
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key
```

### Installation

1. Clone this repository:
```bash
git clone https://github.com/atlanhq/atlan-sample-apps.git
cd giphy
```

2. Install dependencies:
```bash
make install
```

This will:
- Configure git to use HTTPS
- Set up poetry with project-specific virtualenv
- Install all dependencies

## Running the Application

### Start Dependencies
Start Temporal and Dapr services:
```bash
make start-deps
```

### Run the Application
1. Activate the virtual environment:
```bash
source .venv/bin/activate
```

2. Start the application:
```bash
make run
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

### Available Make Commands
- `make install` - Install dependencies and set up the development environment
- `make start-deps` - Start Temporal and Dapr services
- `make run` - Run the application
- `make stop-all` - Stop all services

## Learning Resources
- [Temporal Documentation](https://docs.temporal.io/)
- [Atlan Application SDK Documentation](https://github.com/atlanhq/application-sdk/tree/main/docs)
- [Python FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Giphy API Documentation](https://developers.giphy.com/docs/api)
- [SendGrid Documentation](https://docs.sendgrid.com/)

## Contributing
We welcome contributions! Please feel free to submit a Pull Request.


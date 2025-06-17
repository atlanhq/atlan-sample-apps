# Asset Description Reminder

A workflow application that helps remind asset owners to add descriptions to their assets by sending them Slack messages when assets are found without descriptions.

## Features

- 🏢 **Tenant User Management**: Fetch and display list of users in your Atlan tenant
- 📊 **Asset Discovery**: Find up to 50 assets owned by a selected user
- 🔍 **Description Validation**: Identify assets missing descriptions
- 💬 **Slack Integration**: Send personalized reminder messages via Slack DM
- 🌐 **Web Interface**: User-friendly frontend for selecting users and triggering workflows

## How It Works

The application follows a 4-step workflow:

1. **Fetch User Assets**: Retrieves up to 50 assets owned by the selected user from Atlan
2. **Find Missing Descriptions**: Identifies the first asset without a description
3. **Slack User Lookup**: Finds the user in your Slack workspace (assuming Atlan username matches Slack username)
4. **Send Reminder**: Sends a friendly DM to the user about the missing description

## Setup

### Prerequisites

- Atlan instance with API access
- Slack workspace with a bot token
- Python 3.11+

### Environment Variables

Create a `.env` file in the project root with:

```env
# Required - Atlan Configuration
ATLAN_BASE_URL=https://your-tenant.atlan.com
ATLAN_API_KEY=your-atlan-api-key

# Optional - Slack Configuration (uses mock data if not provided)
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token

# Optional - Auto-start example workflow
AUTO_START_EXAMPLE=false
EXAMPLE_USERNAME=john.doe
```

### Slack Bot Setup

1. Go to [Slack API](https://api.slack.com/apps) and create a new app
2. Navigate to "OAuth & Permissions"
3. Add the following scopes:
   - `chat:write` - Send messages
   - `users:read` - Get user information
   - `channels:read` - Access channel information
4. Install the app to your workspace
5. Copy the "Bot User OAuth Token" (starts with `xoxb-`)


## Usage

### Web Interface

1. Navigate to `http://localhost:8001`
2. Select a user from the dropdown
3. Click "Send Reminder"
4. View the workflow results

### API Usage

You can also trigger workflows programmatically:

```bash
curl -X POST http://localhost:8001/workflows/v1/start \
  -H "Content-Type: application/json" \
  -d '{"user_username": "john.doe"}'
```

### Get Users API

Fetch list of tenant users:

```bash
curl http://localhost:8001/api/v1/users
```

## Development

### Project Structure

```
asset-description-reminder/
├── activities/
│   ├── __init__.py
│   └── description_reminder_activities.py  # All workflow activities
├── workflows/
│   ├── __init__.py
│   └── description_reminder_workflow.py    # Main workflow definition
├── frontend/
│   └── templates/
│       └── index.html                      # Web interface
├── application.py                          # Application setup and server
├── main.py                                 # Entry point
└── README.md
```

### Mock Data

If Slack integration is not configured, the application will use mock data for development and testing purposes.

### Development Commands

```bash
# Install dependencies with uv
cd hack-connectors
uv sync --group slack

# Run the application
cd asset-description-reminder
uv run python main.py

# Run with environment variables
cd asset-description-reminder
uv run --env-file ../.env python main.py

# Install additional dependencies
uv add package-name

# Update dependencies
uv sync
```

## Troubleshooting

### Common Issues

1. **"Missing required environment variables"**
   - Ensure `ATLAN_BASE_URL` and `ATLAN_API_KEY` are set

2. **"Slack client not available"**
   - This is normal if `SLACK_BOT_TOKEN` is not set - mock data will be used

3. **"No users found"**
   - Check your Atlan API permissions
   - Verify your tenant has active users

4. **"User not found in Slack"**
   - Ensure the Atlan username matches the Slack username
   - Check that the user is active in your Slack workspace

### Logs

The application logs detailed information about each step of the workflow, including:
- Asset discovery progress
- Slack user matching attempts
- Message sending results

## License

This project is licensed under the Apache License 2.0.
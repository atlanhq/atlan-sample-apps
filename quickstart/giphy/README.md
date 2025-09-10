# Giphy

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
- **AI Integration via Model Context Protocol (MCP)** - Use with Claude or other AI assistants

## AI Integration (MCP)

The Giphy app supports **Model Context Protocol (MCP)**, allowing AI assistants like Claude to directly interact with your app's functionality.

### Available AI Tools

When MCP is enabled, the following tools become available to AI assistants:

- **`fetch_gif`** - Search and retrieve GIFs from Giphy API
- **`send_email`** - Send GIF emails to recipients

### Enable MCP Integration

**Option 1: Environment Variable**

```bash
ENABLE_MCP=true uv run main.py
```

**Option 2: .env File**
Add to your `.env` file:

```env
ENABLE_MCP=true
```

Then run normally:

```bash
uv run main.py
```

When enabled, you'll see:

```
Starting Atlan Giphy App
FastAPI Server: http://localhost:8000
MCP Integration: ENABLED
   • Activities with @mcp_tool will be auto-exposed
   • MCP endpoint: http://localhost:8000/mcp
   • Available tools: fetch_gif, send_email
   • Debug with MCP Inspector using streamable HTTP
   • For Claude Desktop: Use npx mcp-remote http://localhost:8000/mcp
```

### Use with Claude Desktop

1. **Start the Giphy app with MCP enabled:**

   ```bash
   ENABLE_MCP=true uv run main.py
   ```

2. **Add to Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

   ```json
   {
     "mcpServers": {
       "Atlan Giphy": {
         "command": "npx",
         "args": ["mcp-remote", "http://localhost:8000/mcp"]
       }
     }
   }
   ```

3. **Restart Claude Desktop** and try asking:
   - _"Fetch a funny cat GIF"_
   - _"Send a happy birthday GIF to user@example.com"_

### Debug with MCP Inspector

Visit the [MCP Inspector](https://modelcontextprotocol.io/legacy/tools/inspector) and connect to:

```
http://localhost:8000/mcp
```

This allows you to test MCP tools directly in your browser.

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

# AI Integration (Optional)
ENABLE_MCP=true  # Enable Model Context Protocol for AI assistants
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
├── app/                # Core application logic
│   ├── activities.py   # Workflow activities
│   └── workflow.py     # Workflow definitions
├── frontend/           # Frontend assets
│   ├── static/        # Static files (CSS, JS)
│   └── templates/     # HTML templates
├── local/              # Local data storage
├── deploy/            # Installation and deployment files
├── tests/              # Test files
├── main.py            # Application entry point
├── pyproject.toml     # Dependencies and config
└── README.md          # This file
```

> [!NOTE]
> Make sure you have a `.env` file that matches the [.env.example](.env.example) file in this directory.

<<<<<<< HEAD
> [!TIP]
> Want to containerize this app? See the [Build Docker images](https://github.com/atlanhq/atlan-sample-apps/tree/main/README.md#build-docker-images) section in the repository root README for unified build and run instructions.


=======
>>>>>>> 4f40aaa (feat: integrate MCP support using Application SDK decorators)
## Learning Resources

- [Temporal Documentation](https://docs.temporal.io/)
- [Atlan Application SDK Documentation](https://github.com/atlanhq/application-sdk/tree/main/docs)
- [Python FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Giphy API Documentation](https://developers.giphy.com/docs/api)
- [SendGrid Documentation](https://docs.sendgrid.com/)
- [Model Context Protocol (MCP) Documentation](https://modelcontextprotocol.io/)
- [FastMCP Framework Documentation](https://gofastmcp.com/)
- [MCP Inspector Tool](https://modelcontextprotocol.io/legacy/tools/inspector)

## Contributing

We welcome contributions! Please feel free to submit a Pull Request.

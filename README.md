# Atlan Sample Apps

Sample apps built using [Atlan Application SDK](https://github.com/atlanhq/application-sdk)

## Usage

### Setting up your environment

1. Clone the repository:
   ```bash
   git clone https://github.com/atlanhq/atlan-sample-apps.git
   cd atlan-sample-apps
   ```

2. Follow the setup instructions for your platform:
   - [macOS Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/MAC.md)
   - [Linux Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/LINUX.md)
   - [Windows Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/WINDOWS.md)

3. Install dependencies:
   ```bash
   uv sync --all-groups
   ```

3. Download required components:
   ```bash
   uv run poe download-components
   ```

4. Start the dependencies (in a separate terminal):
   ```bash
   uv run poe start-deps
   ```

5. That loads all required dependencies. To run a sample, you just run the command in the main terminal. For example:
   ```bash
   cd hello_world
   uv run main.py
   ```

Some examples require extra dependencies. See each sample's directory for specific instructions.

> [!NOTE]
> If you are switching between examples, please clear your browser's cache and hard refresh to avoid any issues with the cached static files.


### Sample Apps

| Sample App | Description | Directory |
|------------|-------------|-----------|
| 🤖 AI Giphy | An AI-powered application that allows sending GIFs via email using natural language | [ai_giphy](./ai_giphy) |
| 👋 Hello World | A basic example demonstrating the fundamental concepts of the Atlan Application SDK along with the use of both async and sync activities in a workflow. | [hello_world](./hello_world) |
| 🤡 Giphy | An application that allows sending GIFs via email using Python and Temporal workflows | [giphy](./giphy) |
| 🗃️ MySQL | An application that extracts metadata from a MySQL database and transforms it into a standardized format | [mysql](./mysql) |
| 📈 Workflows Observability | An application that retrieves and logs workflow run metadata from Atlan | [workflows_observability](./workflows_observability) |


## Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for guidelines.

## Need Help?

Get support through any of these channels:

- Email: **connect@atlan.com**
- Issues: [GitHub Issues](https://github.com/atlanhq/atlan-sample-apps/issues)

## Security

Have you discovered a vulnerability or have concerns about this repository? Please read our [SECURITY.md](./SECURITY.md) document for guidance on responsible disclosure, or Please e-mail security@atlan.com and we will respond promptly.

## License

This repository is licensed under the [Apache-2.0 License](./LICENSE).

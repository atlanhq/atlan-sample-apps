# Atlan Sample Apps

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/atlanhq/atlan-sample-apps)

Sample apps built using [Atlan Application SDK](https://github.com/atlanhq/application-sdk)


- [Atlan Sample Apps](#atlan-sample-apps)
  - [Quick Start](#quick-start)
    - [Sample Apps](#sample-apps)
  - [Debugging](#debugging)
  - [Build Docker images](#build-docker-images)
    - [Setup the App Directory](#setup-the-app-directory)
    - [Build the Docker Image](#build-the-docker-image)
    - [Build the multi-platform Docker image](#build-the-multi-platform-docker-image)
    - [Run the Docker container:](#run-the-docker-container)
  - [Contributing](#contributing)
  - [Need Help?](#need-help)
  - [Security](#security)
  - [License](#license)


## Quick Start

Each sample app is **self-contained** with its own dependencies and setup instructions. This makes it easy to run individual apps without installing unnecessary dependencies.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/atlanhq/atlan-sample-apps.git
   cd atlan-sample-apps
   ```

2. **Navigate to any sample app directory:**

   ```bash
   cd quickstart/hello_world  # or any other app directory
   ```

3. **Follow the app's README for specific setup:**
   Each app has its own `README.md` with complete setup instructions

OR

4. Using **[Cursor IDE](https://cursor.com/) (v1.6+)**, you can use slash commands to quickly set up and run sample apps, example:

```
help me /setup and run the mysql /app
```

This will automatically handle the environment setup and app initialization for you!

> [!NOTE]
>
> - Each app has its own environment variables and configuration requirements
> - Always check the README.md file in each app directory for specific instructions
> - When switching between apps, clear your browser cache to avoid cached static files (<kbd>Cmd</kbd> + <kbd>Shift</kbd> + <kbd>R</kbd>)

### Sample Apps

| Sample App                    | Description                                                                                                                                             | Directory                                                                    |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 🤖 AI Giphy                   | An AI-powered application that allows sending GIFs via email using natural language                                                                     | [quickstart/ai_giphy](./quickstart/ai_giphy)                                 |
| 👋 Hello World                | A basic example demonstrating the fundamental concepts of the Atlan Application SDK along with the use of both async and sync activities in a workflow. | [quickstart/hello_world](./quickstart/hello_world)                           |
| 🤡 Giphy                      | An application that allows sending GIFs via email using Python and Temporal workflows                                                                   | [quickstart/giphy](./quickstart/giphy)                                       |
| 🗃️ MySQL                      | An application that extracts metadata from a MySQL database and transforms it into a standardized format                                                | [connectors/mysql](./connectors/mysql)                                       |
| 📈 Anaplan | An application that extracts metadata from an Anaplan instance and transforms it into a standardized format. Intended as an example on how to build apps for non-sql data sources using the Application SDK | [connectors/anaplan](./connectors/anaplan) |
| 📈 Workflows Observability    | An application that retrieves and logs workflow run metadata from Atlan                                                                                 | [utilities/workflows_observability](./utilities/workflows_observability)     |
| 📝 Asset Description Reminder | An application that helps maintain data quality by reminding asset owners to add descriptions to their assets through Slack messages                    | [utilities/asset_descriptor_reminder](./utilities/asset_descriptor_reminder) |
| ⏰ Freshness Monitor          | An application that monitors the freshness of assets in Atlan and sends notifications when assets become stale                                          | [utilities/freshness_monitor](./utilities/freshness_monitor)                 |

## Debugging

- If you use [Cursor](https://cursor.com/) or [VSCode](https://code.visualstudio.com/) IDE, the repository has a launch configuration setup; just update the app directory and run the launch configuration.
- For example, the configuration is defaulted to run the MySQL app, you can click on the "Run App + Deps" launch configuration to run the app along with the dependent services.

## Build Docker images

You can build Docker images for any app in this repo using the provided `Dockerfile`.

### Setup the App Directory

Copy the `Dockerfile` from the root directory to the app directory (example: `connectors/mysql`, `quickstart/ai_giphy`, etc.):

```bash
cp Dockerfile ./connectors/mysql/
```

Navigate to the app directory (for example `connectors/mysql`, `quickstart/ai_giphy`, etc.):

```bash
cd connectors/mysql
```

### Build the Docker Image

From the app directory (for example `connectors/mysql`, `quickstart/ai_giphy`, etc.):

```bash
docker build --no-cache -f ./Dockerfile -t app-name:latest .
```

### Build the multi-platform Docker image

From the app directory (for example `connectors/mysql`, `quickstart/ai_giphy`, etc.):

> [!NOTE]
> We expect app developers to send multi-platform images to Atlan when submitting apps for release.

```bash
docker buildx build --nocache --platform linux/amd64,linux/arm64 -t app-name:latest . --push
```

> [!NOTE]
> If you are using a docker driver which is not docker desktop, make sure that you create a builder and use that for the multi-platform build. You can find the instructions for the same for OrbStack [here](https://docs.orbstack.dev/docker/images#multiplatform) and for Colima [here](https://github.com/abiosoft/colima/issues/44#issuecomment-952281801).

### Run the Docker container:

**If your Temporal service is running on the host machine:**

```bash
docker run -p 8000:8000 --add-host=host.docker.internal:host-gateway -e ATLAN_WORKFLOW_HOST=host.docker.internal -e ATLAN_WORKFLOW_PORT=7233 --user 1000:1000 app-name
```

**If your Temporal service is running elsewhere (remote server/container):**

```bash
docker run -p 8000:8000 -e ATLAN_WORKFLOW_HOST=<your-temporal-host> -e ATLAN_WORKFLOW_PORT=<your-temporal-port> --user 1000:1000 app-name
```

_Replace `<your-temporal-host>` and `<your-temporal-port>` with your actual Temporal service hostname/IP and port._

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

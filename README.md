# Atlan Sample Apps

Sample apps built using [Atlan Application SDK](https://github.com/atlanhq/application-sdk)

## Usage

### Setting up your environment


```
uv sync --all-groups

poe download-components
poe start-deps

poe stop-deps


cd hello_world

uv run main.py
```

- Follow the setup instructions for your platform:
   - [Windows](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/WINDOWS.md)
   - [Mac](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/MAC.md)
   - [Linux](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/LINUX.md)


### Follow instructions for each sample app

| Sample App | Description | Directory |
|------------|-------------|-----------|
| 👋 Hello World | A basic example demonstrating the fundamental concepts of the Atlan Application SDK | [hello_world](./hello_world) |
| 🤡 Giphy | An application that allows sending GIFs via email using Python and Temporal workflows | [giphy](./giphy) |
| 🗃️ MySQL | An application that extracts metadata from a MySQL database and transforms it into a standardized format | [mysql](./mysql) |

## Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for guidelines.

## Need Help?

Get support through any of these channels:

- Email: **connect@atlan.com**
- Slack: **#pod-app-framework**
- Issues: [GitHub Issues](https://github.com/atlanhq/atlan-sample-apps/issues)

## Security

Have you discovered a vulnerability or have concerns about this repository? Please read our [SECURITY.md](./SECURITY.md) document for guidance on responsible disclosure, or Please e-mail security@atlan.com and we will respond promptly.

## License

This repository is licensed under the [Apache-2.0 License](./LICENSE).

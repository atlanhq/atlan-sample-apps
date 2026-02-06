# Atlan CLI: App Command

---

## Overview

The `atlan app` command helps you manage Atlan applications, including initialization, setup, release, and lifecycle management.

```bash
atlan app [subcommand] [options]
```

### Available Subcommands

| Command | Description |
|---------|-------------|
| `init` | Initialize a new Atlan application |
| `template` | Manage application templates |
| `sample` | Manage sample applications |
| `run` | Run the application locally |
| `test` | Run application tests |
| `release` | Package, stage, and validate a Docker image |

---

## `atlan app init`

Initialize a new Atlan application project.

### What it does

1. Installs prerequisites (uv, Temporal, DAPR) via `tools`
2. Downloads a starter template via `template`
3. Creates a virtual environment and installs dependencies via `dependencies`

### Usage

```bash
atlan app init [flags]
atlan app init [subcommand]
```

### Examples

```bash
$ atlan app init                          # Initialize in current directory
$ atlan app init -o my-app                # Initialize in 'my-app' directory
$ atlan app init -o my-app -t generic -y  # Initialize with template and auto-approve
$ atlan app init -s helloworld            # Download helloworld sample app
$ atlan app init -s giphy -o my-giphy     # Download sample to specific directory
```

### Flags

| Flag | Shorthand | Type | Default | Description |
|------|-----------|------|---------|-------------|
| `--output` | `-o` | string | `""` | Directory path to initialize the application |
| `--template` | `-t` | string | `""` | Template to use (run `atlan app template list` to see available) |
| `--sample` | `-s` | string | `""` | Sample app to download (run `atlan app sample list` to see available) |
| `--yes` | `-y` | bool | `false` | Skip confirmation prompts (auto-approve) |
| `--verbose` | `-v` | bool | `false` | Show detailed output during initialization |

---

### `atlan app init tools`

Install prerequisites for Atlan applications.

Installs uv, Temporal CLI, and DAPR. The installation is OS-aware and will use the appropriate installation method for your operating system (macOS, Linux, or Windows).

#### Usage

```bash
atlan app init tools
```

#### Flags

*No flags*

---

### `atlan app init template`

Download and extract an application template.

The destination directory must not already contain files.

#### Usage

```bash
atlan app init template [flags]
```

#### Examples

```bash
$ atlan app init template                       # Scaffold in current directory
$ atlan app init template -o my-app             # Scaffold in 'my-app' directory
$ atlan app init template -o my-app -t generic  # Scaffold with generic template
```

#### Flags

| Flag | Shorthand | Type | Default | Description |
|------|-----------|------|---------|-------------|
| `--output` | `-o` | string | `""` | Directory path to scaffold the application |
| `--template` | `-t` | string | `""` | Template to use (run `atlan app template list` to see available) |

---

### `atlan app init dependencies`

Create a virtual environment and install dependencies.

Creates a Python virtual environment using uv, syncs all dependencies, and downloads required components.

> **Note:** Requires uv to be installed. Run `atlan app init tools` first if you haven't installed the prerequisites.

#### Usage

```bash
atlan app init dependencies [flags]
```

#### Examples

```bash
$ atlan app init dependencies              # Install dependencies in current directory
$ atlan app init dependencies -o my-app    # Install dependencies in 'my-app' directory
```

#### Flags

| Flag | Shorthand | Type | Default | Description |
|------|-----------|------|---------|-------------|
| `--output` | `-o` | string | `""` | Directory path containing the application |

---

## `atlan app run`

Run the application locally for development.

### What it does

1. Starts Temporal and Dapr in the background
2. Runs the application in the foreground
3. Handles graceful shutdown on Ctrl+C

Dependencies are started via `uv run poe start-deps` and stopped via `uv run poe stop-deps` when the application exits.

### Usage

```bash
atlan app run [flags]
```

### Examples

```bash
$ atlan app run                          # Run app in current directory
$ atlan app run --no-watch               # Run without hot reload
$ atlan app run -p ./my-app              # Run app in specified directory
```

### Flags

| Flag | Shorthand | Type | Default | Description |
|------|-----------|------|---------|-------------|
| `--path` | `-p` | string | `.` | Path to app directory |
| `--no-watch` | - | bool | `false` | Disable hot reload (hot reload is enabled by default) |

---

## `atlan app test`

Run application tests.

### Test Types

| Type | Description |
|------|-------------|
| `unit` | Runs unit tests directly via `uv run pytest tests/unit` |
| `e2e` | Starts dependencies, runs the app, waits for healthy, runs `uv run pytest tests/e2e`, then cleans up |
| `all` | Runs unit tests first, then e2e tests (default) |

### Usage

```bash
atlan app test [flags]
```

### Examples

```bash
$ atlan app test                        # Run all tests
$ atlan app test -t unit --coverage     # Run only unit tests with coverage report
$ atlan app test -p ./my-app -v         # Run tests in specified directory with verbose output
```

### Flags

| Flag | Shorthand | Type | Default | Description |
|------|-----------|------|---------|-------------|
| `--path` | `-p` | string | `.` | Path to app directory |
| `--type` | `-t` | string | `all` | Test type: `all`, `unit`, `e2e` |
| `--coverage` | - | bool | `false` | Generate coverage report |
| `--fail-fast` | - | bool | `false` | Stop on first failure |
| `--verbose` | `-v` | bool | `false` | Show detailed output |

---

## `atlan app release`

Package, stage, and validate a Docker image.

### What it does

1. Checks if Docker is running and Dockerfile exists
2. Packages the Docker image
3. Stages to the registry
4. Waits for vulnerability scan and adds label if no critical CVEs

### Usage

```bash
atlan app release <image> [flags]
atlan app release [subcommand]
```

### Examples

```bash
# Release with default settings (prompts for credentials if not saved)
$ atlan app release harbor.atlan.com/myproject/myapp:v1.0.0

# Release from a specific directory with credentials
$ atlan app release harbor.atlan.com/proj/app:v1 -p ./services/api -u myuser --password mypass

# Skip validate phase (useful for CI/CD without credentials)
$ atlan app release harbor.atlan.com/proj/app:v1 --skip-validate

# Dry run: validate setup without building or pushing
$ atlan app release harbor.atlan.com/proj/app:v1 --dry-run
```

### Flags

| Flag | Shorthand | Type | Default | Description |
|------|-----------|------|---------|-------------|
| `--path` | `-p` | string | `.` | Path to Dockerfile directory |
| `--label` | `-l` | string | `replicate-to-ghcr` | Label name to add after validation |
| `--username` | `-u` | string | `""` | Registry username |
| `--password` | - | string | `""` | Registry password |
| `--skip-validate` | - | bool | `false` | Skip vulnerability scan and validate phase |
| `--dry-run` | - | bool | `false` | Validate setup without building or pushing (fast validation) |

---

### `atlan app release package`

Package a Docker image from a Dockerfile.

Validates that Docker is installed and running, checks for a Dockerfile in the specified directory, and builds the image with the given name and tag.

#### Usage

```bash
atlan app release package <image> [flags]
```

#### Examples

```bash
$ atlan app release package harbor.atlan.com/myproject/myapp:v1.0.0
$ atlan app release package harbor.atlan.com/proj/app:v1 -p ./services/api
```

#### Flags

| Flag | Shorthand | Type | Default | Description |
|------|-----------|------|---------|-------------|
| `--path` | `-p` | string | `.` | Path to Dockerfile directory |

---

### `atlan app release stage`

Stage a Docker image to a registry.

Requires registry credentials, which can be provided via flags (`-u`/`--password`), loaded from saved credentials, or prompted interactively. Credentials are automatically saved after successful authentication for future use.

#### Usage

```bash
atlan app release stage <image> [flags]
```

#### Examples

```bash
$ atlan app release stage harbor.atlan.com/myproject/myapp:v1.0.0
$ atlan app release stage harbor.atlan.com/proj/app:v1 -u myuser --password mypass
```

#### Flags

| Flag | Shorthand | Type | Default | Description |
|------|-----------|------|---------|-------------|
| `--username` | `-u` | string | `""` | Registry username |
| `--password` | - | string | `""` | Registry password |

---

### `atlan app release validate`

Check vulnerability scan results and add a label to the image.

#### What it does

1. Waits for Harbor's automatic vulnerability scan to complete
2. Reports the scan results (critical, high, medium vulnerabilities)
3. If no critical CVEs: adds the specified label
4. If critical CVEs found: skips labeling with a warning

#### Usage

```bash
atlan app release validate <image> [flags]
```

#### Examples

```bash
$ atlan app release validate harbor.atlan.com/myproject/myapp:v1.0.0
$ atlan app release validate harbor.atlan.com/proj/app:v1 -u myuser --password mypass
$ atlan app release validate harbor.atlan.com/proj/app:v1 -l production -u myuser --password mypass
```

#### Flags

| Flag | Shorthand | Type | Default | Description |
|------|-----------|------|---------|-------------|
| `--label` | `-l` | string | `replicate-to-ghcr` | Label name to add |
| `--username` | `-u` | string | `""` | Registry username |
| `--password` | - | string | `""` | Registry password |

---

## Quick Reference

### Command Tree

```
atlan app
├── init                    # Initialize a new app
│   ├── tools               # Install prerequisites
│   ├── template            # Download template
│   └── dependencies        # Install dependencies
├── template                # Manage templates
│   └── list                # List available templates
├── sample                  # Manage sample apps
│   └── list                # List available samples
├── run                     # Run locally
├── test                    # Run tests
└── release                 # Full release workflow
    ├── package             # Build Docker image
    ├── stage               # Push to registry
    └── validate            # Check scan & add label
```

### Common Workflows

| Task | Command |
|------|---------|
| Create new app | `atlan app init -o my-app` |
| Start development | `atlan app run` |
| Run all tests | `atlan app test` |
| Release to registry | `atlan app release harbor.atlan.com/proj/app:v1.0.0` |

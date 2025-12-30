# 🔀 Polyglot

A demonstration app showcasing Python-Java integration using JPype. Built with Application SDK.

## Prerequisites

- Python 3.11+
- Java JDK 11+ (required for JPype)
- [uv](https://docs.astral.sh/uv/) package manager
- [Dapr CLI](https://docs.dapr.io/getting-started/install-dapr-cli/)
- [Temporal CLI](https://docs.temporal.io/cli)

### Installation Guides
- [macOS Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/MAC.md)
- [Linux Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/LINUX.md)
- [Windows Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/WINDOWS.md)

## Quick Start

1. **Build the Java JAR:**
   ```bash
   uv run poe build-java
   ```

2. **Download required components:**
   ```bash
   uv run poe download-components
   ```

3. **Set up environment variables (see below)**

4. **Start dependencies (in separate terminal):**
   ```bash
   uv run poe start-deps
   ```

5. **Run the application:**
   ```bash
   uv run python main.py
   ```

## Features

- Python-Java integration using JPype
- JVM lifecycle management
- Temporal workflow orchestration
- Real-world factorial calculation demo
- Cross-language method invocation
- Safe resource management with context managers

## Environment Variables

Create a `.env` file in the `polyglot` root directory.
Configure Java integration using these environment variables:

```env
# Java home directory (optional)
POLYGLOT_JAVA_HOME=/path/to/java

# Custom JAR path (optional)
POLYGLOT_JAR_PATH=/path/to/factorial-calculator.jar

# JVM memory settings (optional)
POLYGLOT_JVM_MAX_MEMORY=512m
POLYGLOT_JVM_INITIAL_MEMORY=256m
```

**Default Configuration:**
- **JAVA_HOME**: System `JAVA_HOME` or `/usr/lib/jvm/java-17-openjdk`
- **JAR_PATH**: `app/libs/factorial-calculator.jar`
- **JVM_MAX_MEMORY**: `512m`
- **JVM_INITIAL_MEMORY**: `256m`

## Usage

### Web Interface

Open your browser and navigate to:
```
http://localhost:8000
```

Enter a number (0-20) and click "Calculate Factorial" to see the result.

### API Endpoints

**Start a Workflow:**
```bash
curl -X POST http://localhost:8000/workflows/v1/start \
  -H "Content-Type: application/json" \
  -d '{"number": 5}'
```

**Get Workflow Result:**
```bash
curl http://localhost:8000/workflows/v1/result/{workflow_id}
```

**Example Response:**
```json
{
  "status": "completed",
  "result": {
    "calculation_result": {
      "result": 120,
      "input": 5,
      "success": true
    },
    "status": "success"
  }
}
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

### Run Tests with Coverage
```bash
uv run coverage run -m pytest tests/unit/
uv run coverage report
```

### Project Structure

```
polyglot/
├── app/                      # Core application logic
│   ├── activities.py         # Workflow activities
│   ├── workflow.py           # Workflow definitions
│   ├── utils/               # JPype utilities
│   │   ├── config.py        # Configuration management
│   │   └── processor.py     # JVM processor
│   └── libs/                # Java JAR files
│       ├── FactorialCalculator.java  # Java source
│       ├── factorial-calculator.jar  # Compiled JAR
│       └── build.sh         # Build script
├── components/               # Dapr component configs
├── frontend/                 # Frontend assets
│   ├── static/              # Static files (CSS, JS)
│   └── templates/           # HTML templates
├── local/                    # Local data storage
│   ├── dapr/                # Dapr runtime data
│   └── tmp/                 # Temporary files
├── tests/                    # Test files
│   ├── test_activities.py   # Activity tests
│   ├── test_workflow.py     # Workflow tests
│   └── test_java_interop.py # Java integration tests
├── main.py                   # Application entry point
├── pyproject.toml            # Dependencies and config
└── README.md                 # This file
```

> [!NOTE]
> Make sure you have a `.env` file that matches the [.env.template](.env.template) file in this directory.

> [!TIP]
> Want to containerize this app? See the [Build Docker images](https://github.com/atlanhq/atlan-sample-apps/tree/main/README.md#build-docker-images) section in the repository root README for unified build and run instructions.

## How It Works

### JPype Integration

JPype creates a bridge between Python and Java:

1. **JVM Startup**: Python starts a Java Virtual Machine
2. **Classpath Loading**: The JAR file is added to the JVM classpath
3. **Java Class Import**: Python imports Java classes dynamically
4. **Method Invocation**: Python calls Java methods as if they were Python functions
5. **Type Conversion**: JPype handles type conversion between Python and Java

### Example Code Flow

```python
# 1. Start JVM with JAR in classpath
jpype.startJVM(classpath=['app/libs/factorial-calculator.jar'])

# 2. Import Java class (after JVM starts)
from FactorialCalculator import FactorialCalculator

# 3. Call Java static method
result = FactorialCalculator.calculateFactorial(5)  # Returns 120

# 4. Use result in Python
print(f"Factorial: {int(result)}")
```

## Learning Resources

- [Temporal Documentation](https://docs.temporal.io/)
- [Atlan Application SDK Documentation](https://github.com/atlanhq/application-sdk/tree/main/docs)
- [Python FastAPI Documentation](https://fastapi.tiangolo.com/)
- [JPype Documentation](https://jpype.readthedocs.io/)

## Contributing

We welcome contributions! Please feel free to submit a Pull Request.

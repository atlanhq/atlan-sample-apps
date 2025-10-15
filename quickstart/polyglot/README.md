# Polyglot Sample App

A demonstration application showcasing Python-Java integration using **JPype** within the **Atlan Application SDK** framework. This sample app illustrates how to call Java methods from Python code, manage JVM lifecycle, and integrate Java libraries into Python workflows.

## 🎯 Purpose

This polyglot application demonstrates:
- **Cross-language integration**: Calling Java code from Python seamlessly
- **JVM lifecycle management**: Starting, reusing, and managing the Java Virtual Machine
- **Temporal workflows**: Orchestrating polyglot (Python-Java) activities
- **Real-world patterns**: Following best practices from production applications like the Atlan Query Intelligence App

## 📚 Use Cases

Use polyglot (Python-Java) integration when you need to:
- Leverage existing Java libraries without rewriting them in Python
- Execute performance-critical operations in Java
- Integrate with Java-based systems and APIs
- Utilize specialized Java parsers, transformers, or processors

## 🚀 Getting Started

### Prerequisites

1. **Python 3.11+**
   ```bash
   python --version
   ```

2. **Java JDK 11+** (required for JPype)
   ```bash
   java -version
   javac -version
   ```

3. **uv** (Python package manager)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

4. **Dapr CLI** (for local development)
   ```bash
   # macOS
   brew install dapr/tap/dapr-cli
   
   # Linux
   wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash
   ```

5. **Temporal CLI** (for workflow engine)
   ```bash
   # macOS
   brew install temporal
   
   # Linux
   curl -sSf https://temporal.download/cli.sh | sh\
   ```

## 🔧 Configuration

### Environment Variables

Configure Java integration using these environment variables:

```bash
# Java home directory
export POLYGLOT_JAVA_HOME=/path/to/java

# Custom JAR path
export POLYGLOT_JAR_PATH=/path/to/factorial-calculator.jar

# JVM memory settings (optional)
export POLYGLOT_JVM_MAX_MEMORY=512m
export POLYGLOT_JVM_INITIAL_MEMORY=256m
```

### Default Configuration

If environment variables are not set, the application uses these defaults:
- **JAVA_HOME**: System `JAVA_HOME` or `/usr/lib/jvm/java-17-openjdk`
- **JAR_PATH**: `app/libs/factorial-calculator.jar`
- **JVM_MAX_MEMORY**: `512m`
- **JVM_INITIAL_MEMORY**: `256m`

### Installation Steps

#### 1. Build the Java JAR

Build the jar file if not already present.

```bash
uv run poe build-java
```

This will:
- Compile `FactorialCalculator.java`
- Create `factorial-calculator.jar` in `app/libs/`
- Clean up intermediate class files
- Test the JAR file

#### 2. Install Python Dependencies

```bash
# Create virtual environment and install dependencies
uv sync

# Or manually
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

#### 3. Download SDK Components

```bash
uv run poe download-components
```

This downloads the necessary Dapr component configurations from the Application SDK.

#### 4. Start Dependencies

In separate terminal windows:

```bash
# Terminal 1: Start Dapr
uv run poe start-dapr

# Terminal 2: Start Temporal
uv run poe start-temporal
```

Or start both together:
```bash
uv run poe start-deps
```

#### 5. Run the Application

```bash
# Make sure you're in the virtual environment
uv run python main.py
```

The application will start on `http://localhost:8000`

#### 6. Access the Frontend

Open your browser and navigate to:
```
http://localhost:8000
```

## 🎮 Usage

### Web Interface

Enter a number (0-20) and click "Calculate Factorial" to see the result.

### API Endpoints

#### Start a Workflow

```bash
curl -X POST http://localhost:8000/workflows/v1/start \
  -H "Content-Type: application/json" \
  -d '{"number": 5}'
```

Response:
```json
{
  "success": true,
  "message": "Workflow started successfully",
  "data": {
    "workflow_id": "generated-uuid-here",
    "run_id": "..."
  }
}
```

#### Get Workflow Result

```bash
curl http://localhost:8000/workflows/v1/result/{workflow_id}
```

### Example Response

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

## 🧪 Testing

### Run All Tests

```bash
uv run pytest tests/ -v
```

### Run Unit Tests Only

```bash
uv run pytest tests/test_activities.py tests/test_workflow.py -v
```

### Run Integration Tests (requires Java)

```bash
# Make sure Java JAR is built first
uv run pytest tests/test_utils.py -v
```

### Test with Coverage

```bash
uv run coverage run -m pytest tests/
uv run coverage report
uv run coverage html  # Generate HTML report
```

## 📖 How It Works

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

### Context Manager Pattern

The `FactorialProcessor` uses a context manager for safe JVM handling:

```python
with FactorialProcessor(number=5) as processor:
    result = processor.calculate()
    # JVM is guaranteed to be started
    # Resources are properly managed
```


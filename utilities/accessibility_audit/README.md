# Accessibility Audit App

An Atlan sample application that performs comprehensive accessibility audits on web applications using **axe-core** and **WAVE** (Web Accessibility Evaluation Tool).

## Features

- **axe-core Integration**: Automated WCAG 2.1 compliance testing using the industry-standard axe-core library via Playwright
- **WAVE API Integration**: Additional accessibility evaluation using WebAIM's WAVE tool (optional, requires API key)
- **WCAG Level Selection**: Choose between Level A, AA (recommended), or AAA conformance testing
- **Combined Reporting**: Generates a unified report with findings from both tools
- **Scoring System**: Provides an overall accessibility score based on issue severity
- **Actionable Recommendations**: Includes specific recommendations to fix identified issues

## Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) - Python package manager
- [Dapr CLI](https://docs.dapr.io/getting-started/install-dapr-cli/) - For local state management
- [Temporal CLI](https://docs.temporal.io/cli) - For workflow orchestration
- Chromium browser (installed automatically via Playwright)

## Quick Start

### 1. Clone and Navigate

```bash
cd utilities/accessibility_audit
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Install Playwright Browsers

```bash
uv run poe install-playwright
```

### 4. Download Dapr Components

```bash
uv run poe download-components
```

### 5. Start Dependencies (Dapr + Temporal)

```bash
uv run poe start-deps
```

### 6. Set Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 7. Run the Application

```bash
uv run python main.py
```

### 8. Access the UI

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Project Structure

```
accessibility_audit/
├── app/
│   ├── __init__.py
│   ├── activities.py      # axe-core and WAVE audit activities
│   └── workflow.py        # Workflow orchestration
├── frontend/
│   ├── static/
│   │   ├── styles.css
│   │   └── script.js
│   └── templates/
│       └── index.html
├── tests/
│   ├── e2e/
│   │   └── test_accessibility_audit_workflow/
│   │       ├── config.yaml
│   │       └── test_accessibility_audit_workflow.py
│   └── unit/
├── main.py                # Application entry point
├── pyproject.toml         # Dependencies and configuration
├── .env.example           # Environment variables template
└── README.md
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ATLAN_LOCAL_DEVELOPMENT` | Enable local development mode | `true` |
| `ATLAN_APPLICATION_NAME` | Application identifier | `accessibility-audit` |
| `ATLAN_API_KEY` | Atlan API key (for production) | - |
| `ATLAN_BASE_URL` | Atlan instance URL | - |
| `WAVE_API_KEY` | WAVE API key (optional) | - |

### WAVE API Key

To use the WAVE integration, obtain a free API key from [wave.webaim.org/api](https://wave.webaim.org/api/).

## Usage

### Via Web UI

1. Open the application at `http://localhost:8000`
2. Enter the URL you want to audit
3. Select the WCAG conformance level (A, AA, or AAA)
4. Optionally enter your WAVE API key for additional checks
5. Click "Start Accessibility Audit"

### Via API

```bash
curl -X POST http://localhost:8000/workflows/v1/start \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "wcag_level": "AA",
    "wave_api_key": "your-optional-wave-key"
  }'
```

## What Gets Checked

### axe-core Checks

- Color contrast ratios
- Image alt text
- Form labels and inputs
- ARIA attributes and roles
- Keyboard navigation
- Heading hierarchy
- Link and button names
- Document structure

### WAVE Checks (with API key)

- Errors (critical issues)
- Alerts (potential issues)
- Features (accessibility features present)
- Structure elements
- ARIA usage
- Contrast issues

## Report Output

The audit generates a comprehensive report including:

- **Overall Score**: 0-100 based on issue severity
- **Violations List**: Sorted by impact (critical > serious > moderate > minor)
- **Tool-specific Summaries**: Breakdown by axe-core and WAVE
- **Recommendations**: Actionable steps to fix issues

## Development

### Running Tests

```bash
# E2E tests
uv run pytest tests/e2e -v

# Unit tests
uv run pytest tests/unit -v
```

### Stopping Dependencies

```bash
uv run poe stop-deps
```

## Docker

Build and run with Docker:

```bash
docker build -t accessibility-audit .
docker run -p 8000:8000 accessibility-audit
```

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [axe-core Documentation](https://www.deque.com/axe/)
- [WAVE API Documentation](https://wave.webaim.org/api/)
- [Atlan Application SDK](https://github.com/atlanhq/application-sdk)

## License

Apache-2.0

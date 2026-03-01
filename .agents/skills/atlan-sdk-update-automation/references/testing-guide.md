# Testing Guide for SDK Updates

## Testing Philosophy

SDK updates require verification at multiple levels:
1. **Import tests** - Ensure modules load correctly
2. **Unit tests** - Verify core functionality
3. **Integration tests** - Check external interactions
4. **E2E tests** - Full workflow validation (optional due to infrastructure)

## Testing Levels

### Level 1: Minimal (Required)
**Time:** ~2-3 minutes
**Use when:** Patch versions, no breaking changes

**Apps to test:**
- quickstart/hello_world
- utilities/workflows_observability
- connectors/mysql

**Commands:**
```bash
# Import verification
cd quickstart/hello_world
uv run python -c "from application_sdk.io.parquet import ParquetFileWriter; from application_sdk.workflows import workflow; print('✓ OK')"

cd utilities/workflows_observability
uv run python -c "from application_sdk.io.parquet import ParquetFileWriter; from application_sdk.workflows import workflow; print('✓ OK')"

cd connectors/mysql
uv run python -c "from application_sdk.io.parquet import ParquetFileReader; from application_sdk.sql_connectors import SQLConnector; print('✓ OK')"

# Unit tests (representative)
cd quickstart/hello_world && uv run pytest tests/unit/ -v
```

### Level 2: Standard (Recommended)
**Time:** ~10-15 minutes
**Use when:** Minor versions, standard updates

**Apps to test:** All quickstart + 2 connectors

**Commands:**
```bash
# All quickstart apps
for app in hello_world giphy ai_giphy polyglot; do
  echo "Testing quickstart/$app..."
  cd quickstart/$app
  uv run pytest -v
  cd ../..
done

# Representative connectors
cd connectors/mysql && uv run pytest -v
cd ../anaplan && uv run pytest -v

# Utilities (spot check)
cd utilities/workflows_observability && uv run pytest tests/unit/ -v
```

### Level 3: Comprehensive (Thorough)
**Time:** ~30-45 minutes
**Use when:** Major versions, breaking changes detected

**Apps to test:** All 10 apps

**Commands:**
```bash
# All apps systematically
find . -name "pyproject.toml" -not -path "./.venv/*" \
  -not -path "*/site-packages/*" \
  -exec dirname {} \; | while read app; do
  if grep -q "atlan-application-sdk" "$app/pyproject.toml"; then
    echo "Testing $app..."
    cd "$app"
    uv run pytest -v || echo "⚠️ Failures in $app"
    cd - > /dev/null
  fi
done
```

## Import Test Patterns

### Basic Import Test
```python
# Test core SDK imports
from application_sdk.io.parquet import ParquetFileReader, ParquetFileWriter
from application_sdk.io.json import JsonFileReader, JsonFileWriter
from application_sdk.workflows import workflow, activity
from application_sdk.observability.logger_adaptor import get_logger

print("✓ All imports successful")
```

### Connector-Specific Imports
```python
# For SQL connectors
from application_sdk.sql_connectors import SQLConnector
from application_sdk.sql_connectors.auth import get_connection

# For workflow apps
from application_sdk.workflows import workflow
from application_sdk.activities import activity
from application_sdk.common.types import DataframeType
```

### Check for Deprecation Warnings
```bash
uv run python -W all -c "
from application_sdk.io.parquet import ParquetFileWriter
from application_sdk.workflows import workflow
print('✓ No deprecation warnings')
"
```

## Test Result Interpretation

### ✅ Success Indicators
```
=================== X passed, Y skipped in Z.ZZs ===================
✓ All imports successful
No import errors
No new test failures
```

**Action:** Proceed to PR creation

### ⚠️ Expected Failures (Acceptable)
```
=================== X passed, Y failed, Z skipped ===================
tests/e2e/test_workflow.py::test_with_real_db FAILED
  Reason: Connection refused (database not available)
```

**Characteristics:**
- E2E tests failing due to infrastructure
- Database/external service connection errors
- "Connection refused", "timeout", "credentials not found"

**Action:** Document in PR, proceed

### 🚨 Unexpected Failures (Investigate)
```
ImportError: cannot import name 'JsonOutput'
AttributeError: 'ParquetFileWriter' object has no attribute 'write'
TypeError: workflow() missing required argument
```

**Characteristics:**
- Import errors
- API signature changes
- Behavioral regressions in unit tests

**Action:**
1. Check SDK changelog for breaking changes
2. Review failed test code
3. Determine if app code needs updates
4. If SDK regression, report to SDK team

### 🔍 Warnings to Review
```
DeprecationWarning: JsonOutput is deprecated, use JsonFileWriter
FutureWarning: This API will be removed in v3.0
PydanticDeprecatedSince20: Support for class-based config is deprecated
```

**Action:**
- Note in PR description
- Create follow-up issue if needed
- Not blocking for this update

## Test Coverage by App

### hello_world
```bash
cd quickstart/hello_world
uv run pytest -v

# Expected: ~14 tests
# - 4 unit tests (should pass)
# - 10 e2e tests (may skip without infrastructure)
```

**Key areas:**
- Basic workflow execution
- Activity invocation
- Output file creation

### giphy
```bash
cd quickstart/giphy
uv run pytest -v

# Expected: ~18 tests
# - 5 unit tests (should pass)
# - 10 e2e tests (may skip)
```

**Key areas:**
- API integration patterns
- Workflow state management
- Error handling

### mysql
```bash
cd connectors/mysql
uv run pytest -v

# Expected: ~13 tests
# - 9 unit tests (should pass)
# - 4 e2e tests (likely fail without MySQL)
```

**Key areas:**
- SQL connector base functionality
- Metadata extraction patterns
- Preflight checks

### workflows_observability
```bash
cd utilities/workflows_observability
uv run pytest tests/unit/ -v

# Expected: unit tests only
```

**Key areas:**
- Workflow monitoring
- Activity tracking
- State management

## CI/CD Integration

### GitHub Actions Tests
After PR creation, CI will run:
```yaml
- E2E tests (if labeled)
- Linting checks
- Security scans (Trivy)
```

**Expected behavior:**
- E2E may fail (infrastructure dependent)
- Linting should pass
- Security scans should pass

### Pre-commit Hooks
If pre-commit is configured:
```bash
cd <app>
uv run pre-commit run --files <changed_file>
```

**Common checks:**
- Code formatting (black, isort)
- Type checking (pyright)
- Linting (ruff)

## Performance Testing (Optional)

### Import Time
```bash
time uv run python -c "from application_sdk.workflows import workflow"
```

**Baseline:** <500ms
**Concern if:** >2s (investigate lazy loading issues)

### Startup Time
```bash
time uv run python app/main.py --help
```

**Baseline:** <2s
**Concern if:** >5s (check for blocking I/O)

## Debugging Failed Tests

### Capture Full Output
```bash
uv run pytest -vv --tb=long --log-cli-level=DEBUG
```

### Run Single Test
```bash
uv run pytest tests/unit/test_specific.py::test_function_name -vv
```

### Interactive Debugging
```bash
uv run pytest tests/unit/test_specific.py::test_function_name --pdb
```

### Check Test Environment
```bash
uv run pytest --collect-only  # Show all tests
uv run pytest --markers       # Show available markers
uv pip list | grep atlan      # Verify SDK version
```

## Test Automation Script

Create a reusable test runner:

```bash
#!/bin/bash
# test-sdk-update.sh

set -e

APPS=(
  "quickstart/hello_world"
  "quickstart/giphy"
  "connectors/mysql"
)

echo "🧪 Testing SDK Update"
echo "===================="

for app in "${APPS[@]}"; do
  echo ""
  echo "Testing $app..."
  cd "$app"

  # Import test
  if uv run python -c "from application_sdk.workflows import workflow; print('✓ Imports OK')"; then
    echo "✅ Import test passed"
  else
    echo "❌ Import test failed"
    exit 1
  fi

  # Unit tests
  if uv run pytest tests/unit/ -v --tb=short; then
    echo "✅ Unit tests passed"
  else
    echo "⚠️ Some unit tests failed"
  fi

  cd - > /dev/null
done

echo ""
echo "✅ Testing complete!"
```

## Test Report Template

Include in PR description:

```markdown
## Testing Summary

### Import Verification
- ✅ hello_world: All imports successful
- ✅ workflows_observability: All imports successful
- ✅ mysql: All imports successful

### Unit Tests
- ✅ hello_world: 4 passed, 10 skipped (e2e)
- ✅ giphy: 8 passed, 10 skipped (e2e)
- ✅ mysql: 9 passed, 4 failed (infrastructure)

### Test Environment
- Python: 3.13.11
- uv: 0.5.x
- OS: macOS / Ubuntu

### Notable Observations
- E2E tests skipped (expected - no test infrastructure)
- No import errors detected
- No new unit test failures
- All core functionality verified

### Coverage
**Level:** Standard (3 apps tested)
**Confidence:** High ✅
```

## Continuous Monitoring

After merge, monitor:
- Production deployments
- Error tracking (if available)
- Performance metrics
- User reports

If issues arise post-merge:
1. Create hotfix branch
2. Revert problematic changes
3. Document root cause
4. Plan proper fix

## Reference Examples

See PR #148 for example test results:
- Import verification: quickstart/hello_world:tests
- Unit tests: quickstart/giphy:tests
- Connector tests: connectors/mysql:tests

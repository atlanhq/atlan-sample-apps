# Common Issues and Fixes

## Issue 1: PyArrow Version Constraint Conflict

### Symptom
```
× No solution found when resolving dependencies:
╰─▶ Because atlan-application-sdk==2.4.1 depends on pyarrow>=20.0.0,<23.0.0
    and your project depends on pyarrow>=23.0.0, we can conclude
    that your project's requirements are unsatisfiable.
```

### Root Cause
- SDK has specific pyarrow version requirements (varies by SDK version)
- Apps were explicitly specifying newer pyarrow versions
- Constraint conflict prevents resolution

### Solution
Remove explicit pyarrow constraint from app's pyproject.toml dependencies.

**Before:**
```toml
dependencies = [
    "atlan-application-sdk[tests,workflows]==2.4.1",
    "poethepoet",
    "pyarrow>=23.0.0",
]
```

**After:**
```toml
dependencies = [
    "atlan-application-sdk[tests,workflows]==2.4.1",
    "poethepoet",
]
```

The SDK will transitively install the correct pyarrow version.

### Affected Apps (Historical)
During 2.4.1 update, this affected:
- utilities/workflows_observability
- utilities/freshness_monitor
- utilities/asset_descriptor_reminder
- quickstart/hello_world
- quickstart/giphy
- quickstart/ai_giphy
- quickstart/polyglot
- templates/generic

### Prevention
Don't add explicit pyarrow constraints unless required for app-specific functionality.

---

## Issue 2: SDK Extra Dependencies Changed

### Symptom
```
error: Failed to download distributions
error: Failed to build: atlan-application-sdk[pandas]
```

### Root Cause
SDK extras may change between versions (renamed, removed, or added).

### Solution
1. Check SDK release notes for extra changes
2. Update extra specifications in pyproject.toml
3. Common extras:
   - `tests` - testing utilities
   - `workflows` - Temporal workflow support
   - `pandas` - pandas support
   - `daft` - daft dataframe support
   - `sqlalchemy` - SQL database support
   - `iam-auth` - AWS IAM authentication

### Example
If `pandas` extra is removed, switch to `daft` or remove the extra.

---

## Issue 3: Import Paths Changed (Breaking)

### Symptom
```python
ImportError: cannot import name 'JsonOutput' from 'application_sdk.io.json'
```

### Root Cause
SDK v2.0.0 renamed classes:
- `JsonInput` → `JsonFileReader`
- `JsonOutput` → `JsonFileWriter`
- `ParquetInput` → `ParquetFileReader`
- `ParquetOutput` → `ParquetFileWriter`

### Solution
Update import statements and class references:

**Before:**
```python
from application_sdk.io.json import JsonInput, JsonOutput
output = JsonOutput(path=path, ...)
```

**After:**
```python
from application_sdk.io.json import JsonFileReader, JsonFileWriter
output = JsonFileWriter(path=path)
```

### Detection
If imports fail during verification phase, this is likely the issue.

---

## Issue 4: Python Version Compatibility

### Symptom
```
error: Package requires a different Python version
```

### Root Cause
SDK may update minimum Python version requirements.

### Solution
1. Check SDK's `requires-python` in new version
2. Update app's `requires-python` if needed
3. Ensure CI/CD uses compatible Python version

### Current Requirement
SDK 2.x series: Python >=3.11,<3.14

---

## Issue 5: Lock File Conflicts

### Symptom
```
error: uv.lock is out of sync with pyproject.toml
```

### Root Cause
Lock file wasn't regenerated after pyproject.toml changes.

### Solution
```bash
rm uv.lock
uv sync
```

Or force sync:
```bash
uv sync --refresh
```

---

## Issue 6: Transitive Dependency Conflicts

### Symptom
```
× No solution found: package X requires Y>=1.0, but Z requires Y<1.0
```

### Root Cause
SDK's dependencies conflict with app's other dependencies.

### Solution
1. Check which package introduces the conflict
2. Update conflicting dependency if possible
3. If SDK conflict, may need to wait for SDK patch
4. Report to SDK team if blocking

### Investigation
```bash
uv tree | grep <conflicting-package>
```

---

## Issue 7: Test Failures After Update

### Symptom
Previously passing tests now fail.

### Root Cause
- Behavior changes in SDK
- API deprecations
- Configuration changes

### Solution
1. Read changelog for behavior changes
2. Check if test expectations need updating
3. Look for deprecation warnings in test output
4. If real regression, report to SDK team

### Example
SDK 2.4.0 changed preflight check response format - tests checking response structure needed updates.

---

## Issue 8: Missing Components Directory

### Symptom
```
FileNotFoundError: components/*.yaml not found
```

### Root Cause
`download-components` poe task not run or SDK_VERSION mismatch.

### Solution
1. Verify SDK_VERSION in poe tasks matches SDK version
2. Run download-components:
```bash
uv run poe download-components
```

### Prevention
Always update SDK_VERSION env var when updating SDK version.

---

## Issue 9: Windows-Specific Path Issues

### Symptom
```
OSError: [Errno 63] File name too long
```

### Root Cause
Windows 260 character path limit.

### Solution
SDK 2.3.2+ includes fix. If on older version, update to >=2.3.2.

Workaround for older versions:
```python
# Enable long path support on Windows
import sys
if sys.platform == 'win32':
    import winreg
    # Set LongPathsEnabled registry key
```

---

## Issue 10: Network/Rate Limiting

### Symptom
```
urllib.error.HTTPError: HTTP Error 429: Too Many Requests
```

### Root Cause
Too many PyPI/GitHub API requests in short time.

### Solution
1. Wait and retry
2. Use GitHub token for API requests (higher rate limit)
3. Batch operations to reduce requests

### GitHub Token
```bash
export GITHUB_TOKEN="your_token"
# SDK and scripts will automatically use it
```

---

## Debugging Tips

### Enable Verbose Logging
```bash
uv sync -v
uv run pytest -vv
```

### Check SDK Constraints
```bash
uv pip show atlan-application-sdk
uv pip inspect | grep -A5 atlan-application-sdk
```

### Isolate Problem
Test one app at a time:
```bash
cd quickstart/hello_world
rm -rf .venv uv.lock
uv sync
```

### Compare with Working Version
Keep a copy of working state:
```bash
git stash
# Test old version
git stash pop
# Test new version
```

---

## Escalation Path

If issue can't be resolved:

1. **Document the issue**
   - Exact error message
   - Steps to reproduce
   - Environment details (Python version, OS)

2. **Check existing issues**
   - GitHub Issues: https://github.com/atlanhq/application-sdk/issues
   - SDK changelog for known issues

3. **Report to SDK team**
   - Create GitHub issue with reproduction
   - Include logs and environment info
   - Tag as `bug` if regression

4. **Rollback if blocking**
   - Revert PR
   - Document issue in Linear
   - Wait for SDK patch or workaround

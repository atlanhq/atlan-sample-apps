# Dependency Patterns in Atlan Sample Apps

## SDK Dependency Patterns

### Pattern 1: Workflow App (Basic)
**Example:** quickstart/hello_world

```toml
[project]
dependencies = [
    "atlan-application-sdk[tests,workflows]==2.4.1",
    "poethepoet",
]
```

**Characteristics:**
- Minimal dependencies
- `workflows` extra for Temporal support
- `tests` extra for testing utilities
- No additional database/API dependencies

**Use when:** Simple workflow apps without external integrations

---

### Pattern 2: Workflow App with External API
**Example:** quickstart/giphy, quickstart/ai_giphy

```toml
[project]
dependencies = [
    "atlan-application-sdk[tests,workflows]==2.4.1",
    "poethepoet",
    "httpx~=0.28.1",  # For API calls (giphy)
    # OR
    "langchain>=0.3.25,<1.0.0",  # For AI integrations (ai_giphy)
    "langchain-openai>=0.3.16",
]
```

**Characteristics:**
- Workflow basics + HTTP client
- External API integration (Giphy, OpenAI)
- Version constraints on external libs

**Use when:** Apps making external API calls

---

### Pattern 3: SQL Connector (Standard)
**Example:** connectors/mysql

```toml
[project]
dependencies = [
    "atlan-application-sdk[daft,sqlalchemy,tests,workflows,iam-auth]==2.4.1",
    "poethepoet",
    "aiomysql>=0.3.0",  # Database-specific driver
]
```

**Characteristics:**
- `daft` extra for dataframe operations
- `sqlalchemy` extra for SQL support
- `iam-auth` extra for AWS IAM authentication
- Database-specific async driver

**Use when:** SQL database connectors

---

### Pattern 4: Advanced Connector (Full Stack)
**Example:** connectors/anaplan

```toml
[project]
dependencies = [
    "atlan-application-sdk[daft,iam-auth,pandas,sqlalchemy,tests,workflows]==2.4.1",
    "poethepoet>=0.37.0",
]
```

**Characteristics:**
- All extras included (daft, pandas, sqlalchemy)
- Both dataframe libraries (daft + pandas)
- Full feature set

**Use when:** Complex connectors needing all SDK features

---

### Pattern 5: Polyglot Integration
**Example:** quickstart/polyglot

```toml
[project]
dependencies = [
    "atlan-application-sdk[pandas,tests,workflows]==2.4.1",
    "jpype1>=1.5.0",  # Java bridge
    "poethepoet",
]
```

**Characteristics:**
- `pandas` for dataframe ops
- `jpype1` for Python-Java interop
- Cross-language integration

**Use when:** Integrating with Java libraries

---

### Pattern 6: Monitoring/Observability
**Example:** utilities/workflows_observability

```toml
[project]
dependencies = [
    "atlan-application-sdk[tests,workflows]==2.4.1",
    "httpx~=0.28.1",
    "poethepoet",
]
```

**Characteristics:**
- Workflow monitoring capabilities
- HTTP client for API calls
- No dataframe processing

**Use when:** Utility apps for monitoring/observability

---

## SDK Extras Reference

### Core Extras

| Extra | Purpose | When to Use |
|-------|---------|-------------|
| `tests` | Testing utilities, fixtures | Always (for dev/CI) |
| `workflows` | Temporal workflow support | All workflow-based apps |
| `pandas` | Pandas dataframe support | Apps using pandas DataFrames |
| `daft` | Daft dataframe support | Apps using daft DataFrames |
| `sqlalchemy` | SQL database support | SQL connectors |
| `iam-auth` | AWS IAM authentication | AWS-hosted databases |

### Combining Extras

```toml
# Single extra
"atlan-application-sdk[workflows]"

# Multiple extras
"atlan-application-sdk[tests,workflows]"

# All common extras
"atlan-application-sdk[daft,pandas,sqlalchemy,tests,workflows,iam-auth]"
```

### Choosing Between Pandas and Daft

**Use pandas when:**
- ✅ Small to medium datasets
- ✅ In-memory processing
- ✅ Rich ecosystem needed
- ✅ Legacy code compatibility

**Use daft when:**
- ✅ Large datasets (>1GB)
- ✅ Distributed processing
- ✅ Cloud-native workflows
- ✅ Modern dataframe API preferred

**Use both when:**
- ✅ Complex connector with multiple modes
- ✅ User can choose backend
- ⚠️ Adds dependency weight

---

## Common Dependency Constraints

### Version Pinning Strategies

#### Exact Pin (Rare)
```toml
"atlan-application-sdk==2.4.1"  # Exact version only
```
**Use when:** Critical stability, tested extensively
**Drawback:** No automatic security patches

#### Compatible Release (Recommended)
```toml
"atlan-application-sdk[tests,workflows]==2.4.1"  # Pin with extras
"httpx~=0.28.1"  # Compatible release: >=0.28.1, <0.29.0
```
**Use when:** Balance stability and updates
**Benefit:** Gets patch updates automatically

#### Minimum Version
```toml
"poethepoet>=0.37.0"  # Any version >= 0.37.0
```
**Use when:** Just need minimum features
**Benefit:** Maximum flexibility

#### Range Constraint
```toml
"langchain>=0.3.25,<1.0.0"  # Between 0.3.25 and 1.0.0
```
**Use when:** Known incompatibility in future version
**Benefit:** Prevents breaking changes

---

## Dependency Conflict Patterns

### Pattern A: Transitive Constraint Conflict

**Scenario:**
```
SDK requires: pyarrow>=20.0.0,<23.0.0
App specifies: pyarrow>=23.0.0
→ Conflict!
```

**Resolution:**
Remove app's constraint, let SDK manage it:
```toml
dependencies = [
    "atlan-application-sdk[tests,workflows]==2.4.1",
    # Removed: "pyarrow>=23.0.0"
]
```

---

### Pattern B: Peer Dependency Conflict

**Scenario:**
```
SDK requires: pydantic>=2.0,<3.0
Other lib requires: pydantic>=1.10,<2.0
→ Conflict!
```

**Resolution:**
1. Check if other lib has v2-compatible version
2. Update other lib to compatible version
3. If not possible, may need to wait for SDK/lib updates

---

### Pattern C: Python Version Constraint

**Scenario:**
```
SDK requires: python>=3.11,<3.14
App specifies: python>=3.10
→ SDK won't install on Python 3.10
```

**Resolution:**
Update app's Python requirement:
```toml
[project]
requires-python = ">=3.11,<3.14"
```

---

## Development Dependencies

### Pattern: Separate Dev Groups

```toml
[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "coverage>=7.0.0",
    "pre-commit>=3.0.0",
]
```

**Benefits:**
- Cleaner production dependencies
- Optional installation: `uv sync --group dev`
- Faster CI without dev tools

### Pattern: Pre-commit Tools

```toml
[dependency-groups]
dev = [
    "pre-commit>=3.8.0",
    "isort>=5.13.2",
    "ruff>=0.12.7",
    "pyright>=1.1.403",
]
```

**For:** Code quality enforcement

---

## Lock File Management

### When to Regenerate

**Always regenerate when:**
- ✅ SDK version changes
- ✅ Adding new dependencies
- ✅ Removing dependencies
- ✅ Constraint changes

**Command:**
```bash
uv sync  # Regenerates uv.lock automatically
```

### Lock File in VCS

**Commit uv.lock because:**
- ✅ Reproducible builds
- ✅ Exact dependency versions tracked
- ✅ CI uses same versions as dev
- ✅ Dependency updates visible in PRs

---

## Special Cases

### Case 1: Local SDK Development

For testing SDK changes locally:

```toml
[tool.uv.sources]
atlan-application-sdk = { path = "../application-sdk", editable = true }
```

**Use when:**
- Developing SDK and apps together
- Testing SDK changes before release
- Debugging SDK issues

**Remember:** Comment out before committing!

---

### Case 2: Pre-release SDK Versions

Testing alpha/beta SDK versions:

```toml
dependencies = [
    "atlan-application-sdk[tests,workflows]==3.0.0a1",
]
```

**Use when:**
- Early testing of major versions
- Beta program participation
- Feature preview

**Caution:** Not for production!

---

### Case 3: Git-based SDK Version

Testing specific SDK commit:

```toml
[tool.uv.sources]
atlan-application-sdk = {
    git = "https://github.com/atlanhq/application-sdk",
    rev = "abc123..."
}
```

**Use when:**
- Testing unreleased fix
- Bisecting SDK regression
- Temporary workaround

**Remember:** Switch to PyPI version ASAP!

---

## Dependency Audit

### Regular Health Checks

```bash
# Check for outdated packages
uv pip list --outdated

# Check for security vulnerabilities
uv pip audit

# Inspect dependency tree
uv tree
```

### Clean Up Unused Dependencies

```bash
# Find unused imports
pyright --verifytypes

# Remove and test
# If tests still pass, dependency wasn't needed
```

---

## Migration Patterns

### Migrating from pip to uv

**Before (requirements.txt):**
```
atlan-application-sdk[tests,workflows]==2.4.1
poethepoet
pyarrow>=23.0.0
```

**After (pyproject.toml):**
```toml
[project]
dependencies = [
    "atlan-application-sdk[tests,workflows]==2.4.1",
    "poethepoet",
    "pyarrow>=23.0.0",
]
```

**Migration steps:**
1. Create pyproject.toml with dependencies
2. Run `uv sync` to generate uv.lock
3. Remove requirements.txt
4. Update CI/CD to use `uv`

---

## Best Practices

### DO ✅
- Pin SDK version exactly (`==`)
- Use compatible release for utilities (`~=`)
- Let SDK manage transitive deps (pyarrow, etc.)
- Commit lock files
- Document why constraints exist
- Regular dependency updates

### DON'T ❌
- Don't add constraints without reason
- Don't skip lock file regeneration
- Don't ignore deprecation warnings
- Don't mix local and PyPI SDK sources
- Don't commit with local SDK paths
- Don't ignore conflict errors

---

## Troubleshooting Decision Tree

```
Dependency issue?
├─ SDK won't install
│  ├─ Python version? → Update requires-python
│  ├─ Conflicting constraint? → Remove app constraint
│  └─ Network/auth? → Check credentials/network
│
├─ App won't sync
│  ├─ Lock file stale? → rm uv.lock && uv sync
│  ├─ Transitive conflict? → Check uv tree
│  └─ Constraint issue? → Review pyproject.toml
│
└─ Tests fail after update
   ├─ Import error? → Check SDK changelog for API changes
   ├─ Behavior change? → Review breaking changes
   └─ Env issue? → Verify Python version, clear cache
```

---

## Reference

- SDK Extras: Check SDK's pyproject.toml for available extras
- Version History: https://github.com/atlanhq/application-sdk/releases
- Migration Guides: SDK documentation
- Issue Tracker: https://github.com/atlanhq/application-sdk/issues

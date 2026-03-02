---
name: atlan-sdk-update-automation
description: Autonomously update atlan-application-sdk across all sample apps with changelog analysis, dependency conflict resolution, testing, and PR creation.
---

# Atlan SDK Update Automation

Enables agents to execute SDK updates autonomously with proper verification, conflict resolution, and testing.

## When to Use This Skill

1. User explicitly requests SDK update ("Update SDK to latest version")
2. User references a Linear issue about SDK updates (created by automated workflow)
3. User asks to "handle dependency updates" and SDK is involved

## Prerequisites Check

Before starting, verify:
- Git repository is clean (no uncommitted changes)
- On main branch or explicitly requested branch
- `uv` is available for dependency management
- Python 3.11+ is available

## Workflow Phases

### Phase 1: Discovery & Analysis (Read-Only)

**Goal:** Understand current state and target version with changelog analysis.

**Steps:**
1. **Find all apps with SDK dependencies**
   ```bash
   find . -name "pyproject.toml" -not -path "./.venv/*" -not -path "*/site-packages/*" -exec grep -l "atlan-application-sdk" {} \;
   ```
   Expected apps:
   - utilities/workflows_observability
   - utilities/freshness_monitor
   - utilities/asset_descriptor_reminder
   - quickstart/hello_world
   - quickstart/giphy
   - quickstart/ai_giphy
   - quickstart/polyglot
   - connectors/mysql
   - connectors/anaplan
   - templates/generic

2. **Check current SDK versions**
   ```bash
   grep -h "atlan-application-sdk" quickstart/hello_world/pyproject.toml | head -1
   ```
   Extract version (e.g., `2.4.1`)

3. **Determine target version**
   - If user specified version: use that
   - Otherwise, fetch latest from PyPI:
     ```bash
     python3 -c "import json; import urllib.request; response = urllib.request.urlopen('https://pypi.org/pypi/atlan-application-sdk/json'); data = json.loads(response.read()); print(data['info']['version'])"
     ```

4. **Fetch and analyze changelog**
   - Fetch GitHub release notes:
     ```bash
     curl -s -H "Accept: application/vnd.github+json" \
       "https://api.github.com/repos/atlanhq/application-sdk/releases/tags/v<VERSION>"
     ```
   - Parse `body` field for changelog
   - **Breaking Change Detection:**
     - Keywords: "breaking", "BREAKING CHANGE", "⚠️", "migration", "deprecat"
     - Semver: Major version bump (2.x.x → 3.x.x)
     - If detected: **warn user and ask for confirmation before proceeding**

5. **Report findings to user**
   ```
   📊 SDK Update Analysis:

   Current Version: 2.4.1
   Target Version:  2.5.0
   Apps Affected:   10

   📝 Changelog Summary:
   - Feature: File upload/download support
   - Fix: Pandas extra compatibility
   - No breaking changes detected ✅

   Proceed with update? [y/n]
   ```

### Phase 2: Update Execution

**Goal:** Update all pyproject.toml files with new SDK version.

**Steps:**
1. **Create feature branch**
   ```bash
   git checkout -b chore/update-sdk-to-<VERSION>
   ```

2. **Update each pyproject.toml**
   - Update SDK version in `dependencies` array
   - Update `SDK_VERSION` env var in `tool.poe.tasks.download-components`
   - Example pattern to replace:
     ```toml
     # Before
     "atlan-application-sdk[tests,workflows]==2.4.1"
     env = { SDK_VERSION = "v2.4.1" }

     # After
     "atlan-application-sdk[tests,workflows]==2.5.0"
     env = { SDK_VERSION = "v2.5.0" }
     ```

3. **Handle dependency conflicts**

   **Common Issue: PyArrow Constraint Conflict**

   SDK versions may have specific pyarrow constraints. Check for conflicts:
   - SDK 2.4.x requires: `pyarrow>=20.0.0,<23.0.0`
   - Apps may specify: `pyarrow>=23.0.0`

   **Resolution:** Remove explicit pyarrow constraints from apps (SDK will handle it)

   See: `references/common-issues.md` for detailed examples

4. **Track update progress**
   Keep a mental checklist of which apps were updated:
   - [ ] utilities/workflows_observability
   - [ ] utilities/freshness_monitor
   - [ ] utilities/asset_descriptor_reminder
   - [ ] quickstart/hello_world
   - [ ] quickstart/giphy
   - [ ] quickstart/ai_giphy
   - [ ] quickstart/polyglot
   - [ ] connectors/mysql
   - [ ] connectors/anaplan
   - [ ] templates/generic

### Phase 3: Dependency Sync

**Goal:** Update lock files and resolve dependencies.

**Steps:**
1. **Run uv sync in each app**
   ```bash
   cd <app_directory> && uv sync
   ```

2. **Monitor for errors**
   - Dependency conflicts → see `references/common-issues.md`
   - Version incompatibilities → check SDK release notes
   - Network issues → retry with exponential backoff

3. **Collect sync results**
   Track which apps synced successfully:
   ```
   ✅ utilities/workflows_observability - synced
   ✅ utilities/freshness_monitor - synced
   ❌ connectors/mysql - conflict detected
   ```

4. **Resolve conflicts if any**
   - Re-read error messages carefully
   - Check for conflicting version constraints
   - Apply fixes from `references/common-issues.md`
   - Re-run `uv sync`

### Phase 4: Verification & Testing

**Goal:** Verify imports work and core functionality is intact.

**Testing Strategy:**
- **Minimal (fastest):** 2-3 representative apps
- **Standard (recommended):** All quickstart apps + 1-2 connectors
- **Comprehensive:** All 10 apps (use for major version bumps)

**Steps:**
1. **Test imports in representative apps**
   ```bash
   cd utilities/workflows_observability
   uv run python -c "from application_sdk.io.parquet import ParquetFileWriter; from application_sdk.workflows import workflow; print('✓ Imports successful')"
   ```

   Test at minimum:
   - `utilities/workflows_observability`
   - `quickstart/hello_world`
   - `connectors/mysql` or `connectors/anaplan`

2. **Run unit tests (standard selection)**
   ```bash
   cd quickstart/hello_world && uv run pytest -v
   cd quickstart/giphy && uv run pytest -v
   cd connectors/mysql && uv run pytest -v
   ```

   Expected results:
   - Unit tests should pass
   - E2E tests may be skipped (require infrastructure)
   - Some failures acceptable if infrastructure-related

3. **Analyze test results**
   - **All pass:** ✅ Proceed to PR
   - **Import errors:** 🚨 Breaking changes, investigate
   - **Infrastructure failures:** ⚠️ Expected, document and proceed
   - **New test failures:** 🔍 Review changelog, may be breaking

4. **Document test results**
   Save for PR description:
   ```
   Testing Summary:
   - hello_world: 4 passed, 10 skipped (e2e)
   - giphy: 8 passed, 10 skipped (e2e)
   - mysql: 9 passed, 4 failed (infrastructure)

   ✅ All imports verified
   ✅ Core functionality intact
   ```

### Phase 5: PR Creation

**Goal:** Create comprehensive PR with all context.

**Steps:**
1. **Stage and commit changes**
   ```bash
   git add -A
   git status  # Verify changes
   git commit -m "update SDK to v<VERSION> across all apps"
   ```

2. **Push branch**
   ```bash
   git push -u origin chore/update-sdk-to-<VERSION>
   ```

3. **Create PR with comprehensive body**
   ```bash
   gh pr create --title "Update SDK to v<VERSION> across all apps" --body "<body>"
   ```

   **PR Body Template:**
   ```markdown
   ## Summary
   Updates atlan-application-sdk from v<OLD> to v<NEW> across all sample apps and resolves dependency conflicts.

   ## Changes
   - Updated SDK version from <OLD> to <NEW> in all pyproject.toml files
   - Updated SDK_VERSION environment variable in poe tasks to v<NEW>
   - [If applicable] Removed conflicting pyarrow constraints
   - Refreshed all uv.lock files with latest compatible dependencies

   ## Apps Updated (10)
   **Utilities:**
   - workflows_observability
   - freshness_monitor
   - asset_descriptor_reminder

   **Quickstart:**
   - hello_world
   - giphy
   - ai_giphy
   - polyglot

   **Connectors:**
   - mysql
   - anaplan

   **Templates:**
   - generic

   ## Breaking Changes
   [✅ No breaking changes | ⚠️ Breaking changes detected - see details below]

   ## SDK Changelog (<OLD> → <NEW>)
   <Insert changelog summary>

   ## Testing
   ✅ All imports verified successfully
   ✅ Unit tests passing (<details>)
   ✅ Dependencies synced successfully in all apps

   <Insert test results>

   ## Reference
   - Linear issue: [if applicable]
   - SDK Release: https://github.com/atlanhq/application-sdk/releases/tag/v<NEW>
   - Previous update PR: #148
   ```

4. **Link to Linear issue if exists**
   If triggered from Linear issue, add comment:
   ```
   PR created: <PR_URL>
   ```

### Phase 6: Post-PR Actions

**Goal:** Ensure PR is ready for review.

**Steps:**
1. **Verify PR created successfully**
   - Check PR URL is valid
   - Verify all commits are included
   - Ensure CI checks are triggered

2. **Monitor initial CI results**
   - Wait for ~1-2 minutes
   - Check if any immediate failures
   - If failures, investigate and update PR

3. **Communicate to user**
   ```
   ✅ SDK update complete!

   📦 Updated SDK from v<OLD> to v<NEW>
   🔧 Updated 10 apps
   ✅ All tests passing
   🎫 PR created: <URL>

   Next steps:
   - PR is ready for review
   - CI checks are running
   - Merge when approved
   ```

## Rollback Strategy

If critical issues found during any phase:

**Before Commit:**
```bash
git restore .
git clean -fd
git checkout main
git branch -D chore/update-sdk-to-<VERSION>
```

**After Commit, Before Push:**
```bash
git reset --hard origin/main
git branch -D chore/update-sdk-to-<VERSION>
```

**After Push:**
- Close PR with explanation
- Document issues found
- Create Linear issue for manual review

## Hard Rules

1. **Never skip changelog analysis** - Always fetch and review before updating
2. **Always warn about breaking changes** - Get user confirmation if detected
3. **Never remove dependency constraints blindly** - Understand why they exist first
4. **Always run at least minimal tests** - Import tests + 2-3 unit test suites
5. **Never force push** - Always create clean commits
6. **Reference PR #148** - Use as gold standard example
7. **Document everything** - PR body should be comprehensive

## Decision Tree

```
Start
  │
  ├─> User specifies version?
  │   ├─ Yes → Use specified version
  │   └─ No → Fetch latest from PyPI
  │
  ├─> Breaking changes detected?
  │   ├─ Yes → Warn user, get confirmation
  │   └─ No → Proceed automatically
  │
  ├─> Dependency conflicts during sync?
  │   ├─ Yes → Apply fixes from references/common-issues.md
  │   └─ No → Continue
  │
  ├─> Test failures detected?
  │   ├─ Import errors → STOP, investigate breaking changes
  │   ├─ Infrastructure errors → Document, proceed
  │   ├─ New test failures → Review changelog, consult user
  │   └─ All pass → Proceed to PR
  │
  └─> PR created successfully?
      ├─ Yes → Monitor CI, communicate success
      └─ No → Retry, then escalate to user
```

## Common Patterns

### Pattern 1: Patch Version Update (2.4.1 → 2.4.2)
- Low risk
- No breaking changes expected
- Standard testing sufficient
- Quick review

### Pattern 2: Minor Version Update (2.4.1 → 2.5.0)
- Medium risk
- New features, possible deprecations
- Standard testing + changelog review
- Normal review process

### Pattern 3: Major Version Update (2.4.1 → 3.0.0)
- High risk
- Breaking changes expected
- Comprehensive testing required
- Extended review + team discussion

## References

- Common issues and fixes: `references/common-issues.md`
- Testing procedures: `references/testing-guide.md`
- Example PR: `references/example-pr-148.md`
- Dependency patterns: `references/dependency-patterns.md`

## Success Metrics

A successful SDK update includes:
- ✅ All 10 apps updated with correct versions
- ✅ All lock files regenerated
- ✅ No dependency conflicts remaining
- ✅ Import tests passing in representative apps
- ✅ Unit tests passing (infrastructure failures acceptable)
- ✅ Comprehensive PR created with full context
- ✅ Clear communication to user throughout process

## Example Session

```
User: Update SDK to latest version

Agent: 🔍 Analyzing SDK update requirements...

[Discovery phase - reads files, checks versions, fetches changelog]

Agent: 📊 SDK Update Analysis:

Current Version: 2.4.1
Target Version:  2.4.2
Apps Affected:   10

📝 Changelog Summary:
- Bug fix: Daft writer alignment with pandas behavior
- Fix: Windows path length limitation
- No breaking changes detected ✅

Proceeding with update...

[Update execution - modifies files]

Agent: ✏️ Updated 10 pyproject.toml files
[Dependency sync - runs uv sync]

Agent: 🔄 Syncing dependencies...
✅ All apps synced successfully

[Testing phase]

Agent: 🧪 Running tests...
✅ hello_world: 4 passed, 10 skipped
✅ giphy: 8 passed, 10 skipped
✅ mysql: 9 passed, 4 failed (infrastructure)
✅ All imports verified

[PR creation]

Agent: 📝 Creating PR...
✅ PR created: https://github.com/.../pull/149

🎉 SDK update complete!

Summary:
- Updated from v2.4.1 → v2.4.2
- 10 apps updated
- All tests passing
- PR ready for review
```

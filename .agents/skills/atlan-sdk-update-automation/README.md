# Atlan SDK Update Automation Skill

## Overview
This skill enables agents to autonomously update the `atlan-application-sdk` dependency across all sample apps with proper verification, conflict resolution, and testing.

## Quick Start

### For Agents
```
Update SDK to latest version
```
or
```
Update SDK to v2.5.0
```

The skill will:
1. Fetch and analyze changelog
2. Detect breaking changes
3. Update all 10 apps
4. Resolve dependency conflicts
5. Run comprehensive tests
6. Create a PR with full documentation

### For Humans
Triggered automatically via GitHub Actions workflow when new SDK versions are detected. Creates Linear issues for review.

## Files

### Core Skill
- **`SKILL.md`** - Complete agent workflow with 6 phases:
  - Phase 1: Discovery & Analysis
  - Phase 2: Update Execution
  - Phase 3: Dependency Sync
  - Phase 4: Verification & Testing
  - Phase 5: PR Creation
  - Phase 6: Post-PR Actions

### References
- **`references/common-issues.md`** - 10 common issues with detailed solutions
- **`references/testing-guide.md`** - Testing strategies and procedures
- **`references/example-pr-148.md`** - Real-world PR example as template
- **`references/dependency-patterns.md`** - Dependency management patterns

## Integration Points

### 1. GitHub Actions Workflow
**File:** `.github/workflows/sdk-update-check.yaml`

Runs twice weekly (Tuesday & Friday 9 AM UTC) to:
- Check for new SDK versions
- Analyze changelog for breaking changes
- Create Linear issues with full context

### 2. Python Script
**File:** `.github/scripts/check_sdk_update.py`

Handles:
- PyPI version checking
- GitHub release fetching
- Breaking change detection
- Linear API integration

### 3. Agent Skill
**File:** `.agents/skills/atlan-sdk-update-automation/SKILL.md`

Guides agents through:
- Systematic multi-app updates
- Dependency conflict resolution
- Test execution and analysis
- PR creation with comprehensive documentation

## Workflow Diagram

```
Cron Trigger (2x/week)
        ↓
Check PyPI for updates
        ↓
    ┌───┴───┐
    │       │
No Update  Update Available
    │       ↓
  Exit   Fetch Changelog
          ↓
      Analyze Breaking Changes
          ↓
      Find Affected Apps
          ↓
    Create Linear Issue
          ↓
    [Team Reviews Issue]
          ↓
    [Agent Updates Apps]
          ↓
      Create PR
```

## Example Usage

### Scenario 1: Safe Update
```
Linear Issue Created:
"SDK Update Available: v2.4.1 → v2.4.2"
Priority: Normal
Status: No breaking changes ✅

Developer: "Update SDK to latest"
Agent: [Loads skill, executes workflow]
Result: PR #149 created with all apps updated
```

### Scenario 2: Breaking Changes
```
Linear Issue Created:
"⚠️ SDK Update Available: v2.4.1 → v3.0.0 (Breaking Changes)"
Priority: High
Status: Manual review required

Developer reviews changelog, then:
"Update SDK to v3.0.0 but check for migration notes"
Agent: [Loads skill, warns about breaking changes]
Developer: "Proceed"
Agent: [Executes with extra caution]
Result: PR created with migration notes
```

## Testing Levels

### Minimal (2-3 min)
- Import verification
- 2-3 representative apps
- Basic unit tests

### Standard (10-15 min) - Recommended
- All quickstart apps
- 2 connectors
- Full unit test suite

### Comprehensive (30-45 min)
- All 10 apps
- Complete test coverage
- Use for major versions

## Success Metrics

A successful update includes:
- ✅ All 10 apps updated
- ✅ All lock files regenerated
- ✅ No dependency conflicts
- ✅ Import tests passing
- ✅ Unit tests passing
- ✅ Comprehensive PR created

## Common Issues

### Issue: PyArrow Conflict
**Solution:** Remove explicit pyarrow constraints (see `references/common-issues.md`)

### Issue: Breaking Changes
**Solution:** Review changelog, get user confirmation, document in PR

### Issue: Test Failures
**Solution:** Analyze failures, distinguish infrastructure vs. real issues

See `references/common-issues.md` for 10+ detailed solutions.

## Configuration

### GitHub Secrets Required
```
LINEAR_API_KEY - Your Linear API token
LINEAR_TEAM_ID - Your Linear team ID
```

### Schedule Configuration
Edit `.github/workflows/sdk-update-check.yaml`:
```yaml
schedule:
  - cron: '0 9 * * 2'  # Tuesday 9 AM UTC
  - cron: '0 9 * * 5'  # Friday 9 AM UTC
```

## Related Documentation

- **Workflow README:** `.github/workflows/README-SDK-UPDATE.md`
- **Main Agents Guide:** `AGENTS.md`
- **PR Example:** PR #148

## Maintenance

### Updating the Skill
When SDK update patterns change:
1. Update `SKILL.md` with new patterns
2. Add new issues to `references/common-issues.md`
3. Update testing guide if needed
4. Document in PR references

### Syncing to Claude Skills
After updates, sync to Claude:
```bash
python .agents/skills/_shared/scripts/sync_claude_skills.py
```

## Support

### For Issues
- Check `references/common-issues.md`
- Review PR #148 example
- Consult testing guide

### For Improvements
- Document in Linear issue
- Update skill references
- Create PR with enhancements

## Version History

- **v1.0** (Mar 2026): Initial release
  - 6-phase workflow
  - Automated breaking change detection
  - Comprehensive reference documentation
  - GitHub Actions integration
  - Linear issue creation

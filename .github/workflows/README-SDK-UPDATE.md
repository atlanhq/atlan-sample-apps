# SDK Update Check Workflow

## Overview
This workflow automatically checks for new versions of `atlan-application-sdk` twice a week and creates Linear issues for team review.

## Schedule
- **Tuesday 9:00 AM UTC**
- **Friday 9:00 AM UTC**

Can also be triggered manually via GitHub Actions UI.

## How It Works

1. **Version Check**: Compares current SDK version (from `quickstart/hello_world/pyproject.toml`) with latest PyPI version
2. **Changelog Analysis**: Fetches GitHub release notes and analyzes for breaking changes using:
   - Keyword detection: "breaking", "BREAKING CHANGE", "⚠️", "migration", "deprecat"
   - Semver analysis: Major version bumps indicate breaking changes
3. **App Discovery**: Scans repository for all apps using the SDK
4. **Linear Issue Creation**: Creates a detailed issue with:
   - Version change summary
   - Breaking change analysis
   - Full changelog
   - List of affected apps
   - Link to agent skill documentation
   - Recommended next steps

## Linear Issue Format

### Safe Updates (No Breaking Changes)
- **Title**: `SDK Update Available: v2.4.1 → v2.5.0`
- **Priority**: Normal (3)
- **Labels**: `dependency-update`, `sdk`, `automated`

### Breaking Changes Detected
- **Title**: `⚠️ SDK Update Available: v2.4.1 → v3.0.0 (Breaking Changes Detected)`
- **Priority**: High (1)
- **Labels**: `dependency-update`, `sdk`, `automated`, `breaking-change`

## Required Secrets

Set these in GitHub repository settings:

- `LINEAR_API_KEY`: Your Linear personal API token
  - Get from: https://linear.app/settings/api
- `LINEAR_TEAM_ID`: Your team's Linear ID
  - Get from: https://linear.app/settings/api (in GraphQL explorer, query `teams`)

## Testing

### Manual Trigger
1. Go to Actions tab in GitHub
2. Select "SDK Update Check" workflow
3. Click "Run workflow"

### Local Testing
```bash
# Set environment variables
export LINEAR_API_KEY="your_api_key"
export LINEAR_TEAM_ID="your_team_id"

# Run script
python3 .github/scripts/check_sdk_update.py
```

## Agent Integration

When a Linear issue is created, team members can trigger the SDK update using the agent skill:

```
Update SDK to latest version
```

The agent will:
1. Load the `atlan-sdk-update-automation` skill
2. Execute the update workflow
3. Handle dependency conflicts
4. Run tests
5. Create a PR

## Files

- `.github/workflows/sdk-update-check.yaml`: GitHub Actions workflow
- `.github/scripts/check_sdk_update.py`: Python script for version checking and Linear integration
- `.agents/skills/atlan-sdk-update-automation/SKILL.md`: Agent skill documentation (to be created)

## Troubleshooting

### Issue Not Created
- Check GitHub Actions logs
- Verify secrets are set correctly
- Ensure Linear API key has write permissions

### False Breaking Change Detection
- Review the changelog analysis logic in `check_sdk_update.py`
- Adjust keywords or confidence thresholds as needed

### Too Many Notifications
- Adjust cron schedule in workflow file
- Consider adding filters for patch version updates only

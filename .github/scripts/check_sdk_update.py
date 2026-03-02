#!/usr/bin/env python3
"""
SDK Update Check Script
Checks for new SDK versions and creates Linear issues for team review.
"""

import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path


def get_current_sdk_version():
    """Get current SDK version from hello_world app."""
    pyproject_path = Path("quickstart/hello_world/pyproject.toml")
    content = pyproject_path.read_text()
    match = re.search(r"atlan-application-sdk.*==([0-9.]+)", content)
    if match:
        return match.group(1)
    raise ValueError("Could not find SDK version in pyproject.toml")


def get_latest_sdk_version():
    """Get latest SDK version from PyPI."""
    url = "https://pypi.org/pypi/atlan-application-sdk/json"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read())
        return data["info"]["version"]


def fetch_changelog(version):
    """Fetch changelog from GitHub releases."""
    url = (
        f"https://api.github.com/repos/atlanhq/application-sdk/releases/tags/v{version}"
    )
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            return data.get("body", "Changelog not available"), data.get("html_url", "")
    except Exception as e:
        print(f"Failed to fetch changelog: {e}")
        return (
            "Changelog not available",
            f"https://github.com/atlanhq/application-sdk/releases/tag/v{version}",
        )


def analyze_breaking_changes(changelog, current_version, latest_version):
    """Analyze changelog for breaking changes."""
    breaking_detected = False
    confidence = "low"

    # Check for breaking change keywords
    breaking_keywords = ["breaking", "BREAKING CHANGE", "⚠️", "migration", "deprecat"]
    for keyword in breaking_keywords:
        if keyword.lower() in changelog.lower():
            breaking_detected = True
            confidence = "high"
            break

    # Check semver for major version bump
    current_major = int(current_version.split(".")[0])
    latest_major = int(latest_version.split(".")[0])

    if current_major != latest_major:
        breaking_detected = True
        confidence = "high"

    return breaking_detected, confidence


def find_affected_apps():
    """Find all apps with SDK dependency."""
    result = subprocess.run(
        [
            "find",
            ".",
            "-name",
            "pyproject.toml",
            "-not",
            "-path",
            "./.venv/*",
            "-not",
            "-path",
            "*/site-packages/*",
            "-exec",
            "grep",
            "-l",
            "atlan-application-sdk",
            "{}",
            ";",
        ],
        capture_output=True,
        text=True,
    )

    apps = []
    for path in result.stdout.strip().split("\n"):
        if path:
            app = path.replace("./", "").replace("/pyproject.toml", "")
            apps.append(app)

    return sorted(apps)


def create_linear_issue(title, description, priority):
    """Create a Linear issue via GraphQL API."""
    api_key = os.environ.get("LINEAR_API_KEY")
    team_id = os.environ.get("LINEAR_TEAM_ID")

    if not api_key or not team_id:
        print("❌ LINEAR_API_KEY or LINEAR_TEAM_ID not set")
        return None

    mutation = """
    mutation CreateIssue($teamId: String!, $title: String!, $description: String!, $priority: Int!) {
      issueCreate(
        input: {
          teamId: $teamId
          title: $title
          description: $description
          priority: $priority
        }
      ) {
        success
        issue {
          id
          identifier
          title
          url
        }
      }
    }
    """

    variables = {
        "teamId": team_id,
        "title": title,
        "description": description,
        "priority": priority,
    }

    payload = {"query": mutation, "variables": variables}

    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": api_key},
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            if result.get("data", {}).get("issueCreate", {}).get("success"):
                issue = result["data"]["issueCreate"]["issue"]
                return issue
            else:
                print(f"❌ Failed to create issue: {result}")
                return None
    except Exception as e:
        print(f"❌ Error creating Linear issue: {e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    print("🔍 Checking for SDK updates...")

    # Get versions
    current_version = get_current_sdk_version()
    latest_version = get_latest_sdk_version()

    print(f"Current SDK version: {current_version}")
    print(f"Latest SDK version: {latest_version}")

    # Check if update needed
    if current_version == latest_version:
        print("✅ SDK is up to date")
        return

    print(f"📦 Update available: {current_version} → {latest_version}")

    # Fetch changelog
    changelog, release_url = fetch_changelog(latest_version)

    # Analyze breaking changes
    breaking_detected, confidence = analyze_breaking_changes(
        changelog, current_version, latest_version
    )

    # Find affected apps
    apps = find_affected_apps()
    app_count = len(apps)
    app_list = "\n".join([f"- `{app}`" for app in apps])

    print(f"Found {app_count} apps to update")
    print(f"Breaking changes detected: {breaking_detected} (confidence: {confidence})")

    # Prepare issue content
    if breaking_detected:
        title = f"⚠️ SDK Update Available: v{current_version} → v{latest_version} (Breaking Changes Detected)"
        priority = 1  # High
        recommendation = f"🔍 **Manual review required** - Breaking changes detected with {confidence} confidence. Review changelog carefully before updating."
    else:
        title = f"SDK Update Available: v{current_version} → v{latest_version}"
        priority = 3  # Normal
        recommendation = "✅ **Safe to proceed** - No breaking changes detected. Update can be performed with standard testing."

    # Truncate changelog if too long
    changelog_display = changelog[:2000] + "..." if len(changelog) > 2000 else changelog

    description = f"""## Summary
A new version of `atlan-application-sdk` is available on PyPI.

**Current Version:** `{current_version}`
**Latest Version:** `{latest_version}`
**Apps Affected:** {app_count}

## Breaking Change Analysis
**Status:** {breaking_detected}
**Confidence:** {confidence}

{recommendation}

## Affected Apps
{app_list}

## Changelog
```
{changelog_display}
```

## Resources
- [GitHub Release]({release_url})
- [SDK Changelog](https://github.com/atlanhq/application-sdk/releases)
- [Agent Skill Documentation](.agents/skills/atlan-sdk-update-automation/SKILL.md)

## Next Steps
1. Review the changelog above for breaking changes
2. If safe to proceed, trigger the SDK update automation:
   - Use the `atlan-sdk-update-automation` skill
   - Command: "Update SDK to latest version" or "Update SDK to v{latest_version}"
3. The agent will:
   - Update all pyproject.toml files
   - Handle dependency conflicts
   - Run tests across affected apps
   - Create a PR with all changes

## Reference
- Previous SDK update PR: #148
"""

    # Create Linear issue
    print("🎫 Creating Linear issue...")
    issue = create_linear_issue(title, description, priority)

    if issue:
        print("✅ Linear issue created successfully!")
        print(f"Issue: {issue['identifier']}")
        print(f"URL: {issue['url']}")
    else:
        print("❌ Failed to create Linear issue")
        exit(1)


if __name__ == "__main__":
    main()

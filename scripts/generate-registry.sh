#!/usr/bin/env bash
#
# generate-registry.sh — Build registry.json from atlan-app-registry.json manifests.
#
# Usage:
#   bash scripts/generate-registry.sh [REPO_NAME] [BRANCH]
#
# Arguments (optional, defaults work for local development):
#   REPO_NAME  — GitHub repository full name (default: atlanhq/atlan-sample-apps)
#   BRANCH     — Branch name used to construct zipUrl (default: main)
#
# The script scans the local filesystem for **/atlan-app-registry.json,
# validates each manifest, and writes registry.json at the repo root.
# Exits non-zero on validation errors.

set -euo pipefail

REPO="${1:-atlanhq/atlan-sample-apps}"
BRANCH="${2:-main}"
REPO_NAME=$(echo "$REPO" | cut -d'/' -f2)
SAFE_BRANCH=$(echo "$BRANCH" | tr '/' '-')

REQUIRED_FIELDS="name type published"
ALLOWED_TYPES="template sample"
ALLOWED_PUBLISHED="true false"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

REGISTRY_FILE="$REPO_ROOT/registry.json"

echo '{"templates":{},"samples":{}}' > "$REGISTRY_FILE"

SEEN_NAMES=""
ERRORS=0

MANIFESTS=$(find "$REPO_ROOT" -name "atlan-app-registry.json" -not -path "*/.github/*" -not -path "*/.git/*" -not -path "*/node_modules/*" | sort)

if [ -z "$MANIFESTS" ]; then
  echo "ERROR: No atlan-app-registry.json manifests found"
  exit 1
fi

for MANIFEST in $MANIFESTS; do
  # Display path relative to repo root
  REL_PATH="${MANIFEST#"$REPO_ROOT/"}"
  echo "Processing: $REL_PATH"

  # --- JSON validation ---

  if ! jq empty "$MANIFEST" 2>/dev/null; then
    echo "  ERROR: Invalid JSON"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  # --- Reject unknown fields ---

  ACTUAL_FIELDS=$(jq -r 'keys[]' "$MANIFEST")
  for FIELD in $ACTUAL_FIELDS; do
    if ! echo "$REQUIRED_FIELDS" | grep -qw "$FIELD"; then
      echo "  ERROR: Unknown field '$FIELD' (allowed: $REQUIRED_FIELDS)"
      ERRORS=$((ERRORS + 1))
    fi
  done

  # --- Check required fields and read values ---

  MANIFEST_VALID=true
  NAME=$(jq -r '.name // empty' "$MANIFEST")
  TYPE=$(jq -r '.type // empty' "$MANIFEST")
  PUBLISHED=$(jq -r '.published // empty' "$MANIFEST")

  for FIELD in $REQUIRED_FIELDS; do
    VALUE=$(jq -r --arg f "$FIELD" '.[$f] // empty' "$MANIFEST")
    if [ -z "$VALUE" ]; then
      echo "  ERROR: Missing required field '$FIELD'"
      ERRORS=$((ERRORS + 1))
      MANIFEST_VALID=false
    fi
  done

  # --- Validate field values ---

  if [ -n "$TYPE" ] && ! echo "$ALLOWED_TYPES" | grep -qw "$TYPE"; then
    echo "  ERROR: Invalid type '$TYPE' (must be one of: $ALLOWED_TYPES)"
    ERRORS=$((ERRORS + 1))
    MANIFEST_VALID=false
  fi

  if [ -n "$PUBLISHED" ] && ! echo "$ALLOWED_PUBLISHED" | grep -qw "$PUBLISHED"; then
    echo "  ERROR: Invalid published value '$PUBLISHED' (must be one of: $ALLOWED_PUBLISHED)"
    ERRORS=$((ERRORS + 1))
    MANIFEST_VALID=false
  fi

  if [ "$MANIFEST_VALID" != "true" ]; then
    continue
  fi

  if [ "$PUBLISHED" != "true" ]; then
    echo "  Skipping $NAME (published: false)"
    continue
  fi

  # --- Duplicate detection ---

  QUALIFIED_NAME="${TYPE}:${NAME}"
  if echo "$SEEN_NAMES" | grep -qw "$QUALIFIED_NAME"; then
    echo "  ERROR: Duplicate name '$NAME' for type '$TYPE'"
    ERRORS=$((ERRORS + 1))
    continue
  fi
  SEEN_NAMES="$SEEN_NAMES $QUALIFIED_NAME"

  # --- Add to registry ---

  ZIP_URL="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.zip"
  DIR_PATH=$(dirname "$REL_PATH")
  ARCHIVE_PATH="${REPO_NAME}-${SAFE_BRANCH}/${DIR_PATH}"

  REGISTRY_KEY="${TYPE}s"
  jq --arg key "$REGISTRY_KEY" \
     --arg name "$NAME" \
     --arg zipUrl "$ZIP_URL" \
     --arg path "$ARCHIVE_PATH" \
    '.[$key][$name] = {"zipUrl": $zipUrl, "path": $path}' \
    "$REGISTRY_FILE" > "${REGISTRY_FILE}.tmp" && mv "${REGISTRY_FILE}.tmp" "$REGISTRY_FILE"

  echo "  Added: $NAME ($TYPE)"
done

# Fail if any manifest had errors
if [ "$ERRORS" -gt 0 ]; then
  echo ""
  echo "ERROR: Registry generation failed with $ERRORS error(s)"
  exit 1
fi

# --- Output validation ---

echo ""
echo "Generated registry.json:"
jq . "$REGISTRY_FILE"

if ! jq empty "$REGISTRY_FILE" 2>/dev/null; then
  echo "ERROR: Generated registry.json is not valid JSON"
  exit 1
fi

TEMPLATE_COUNT=$(jq '.templates | length' "$REGISTRY_FILE")
SAMPLE_COUNT=$(jq '.samples | length' "$REGISTRY_FILE")
echo ""
echo "Registry contains $TEMPLATE_COUNT template(s) and $SAMPLE_COUNT sample(s)"

if [ "$TEMPLATE_COUNT" -eq 0 ] && [ "$SAMPLE_COUNT" -eq 0 ]; then
  echo "ERROR: Registry is empty, something went wrong"
  exit 1
fi

INVALID=$(jq -r '
  [.templates, .samples] | add | to_entries[] |
  select(.value.zipUrl == null or .value.path == null) |
  .key
' "$REGISTRY_FILE")

if [ -n "$INVALID" ]; then
  echo "ERROR: The following entries are missing zipUrl or path:"
  echo "$INVALID"
  exit 1
fi

echo "Output validation passed"

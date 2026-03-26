#!/usr/bin/env bash
#
# generate-deploy-scaffolding.sh — Copy shared workflows and generate atlan.yaml
# for every app that has an atlan-app-registry.json manifest.
#
# Usage:
#   bash scripts/generate-deploy-scaffolding.sh
#
# Reads each atlan-app-registry.json, copies build-image.yaml and publish.yaml
# from templates/_shared/workflows/, and generates atlan.yaml from the template
# using the app name from the manifest.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SHARED_DIR="$REPO_ROOT/templates/_shared"
WORKFLOW_SRC="$SHARED_DIR/workflows"
ATLAN_YAML_TEMPLATE="$SHARED_DIR/atlan.yaml.template"

# Validate shared sources exist
for f in "$WORKFLOW_SRC/build-image.yaml" "$WORKFLOW_SRC/publish.yaml" "$ATLAN_YAML_TEMPLATE"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: Missing shared source: $f"
    exit 1
  fi
done

MANIFESTS=$(find "$REPO_ROOT" -name "atlan-app-registry.json" \
  -not -path "*/.github/*" \
  -not -path "*/.git/*" \
  -not -path "*/node_modules/*" \
  -not -path "*/templates/_shared/*" \
  | sort)

if [ -z "$MANIFESTS" ]; then
  echo "ERROR: No atlan-app-registry.json manifests found"
  exit 1
fi

UPDATED=0

for MANIFEST in $MANIFESTS; do
  APP_DIR=$(dirname "$MANIFEST")
  APP_NAME=$(jq -r '.name // empty' "$MANIFEST")

  if [ -z "$APP_NAME" ]; then
    echo "WARN: Skipping $MANIFEST — missing 'name' field"
    continue
  fi

  REL_PATH="${APP_DIR#"$REPO_ROOT/"}"

  # Derive app type from top-level directory
  TOP_DIR=$(echo "$REL_PATH" | cut -d'/' -f1)
  case "$TOP_DIR" in
    connectors) APP_TYPE="connector" ;;
    utilities)  APP_TYPE="utility" ;;
    *)          APP_TYPE="connector" ;;
  esac

  echo "Processing: $REL_PATH ($APP_NAME, type=$APP_TYPE)"

  # Copy workflow files
  mkdir -p "$APP_DIR/.github/workflows"
  cp "$WORKFLOW_SRC/build-image.yaml" "$APP_DIR/.github/workflows/build-image.yaml"
  cp "$WORKFLOW_SRC/publish.yaml" "$APP_DIR/.github/workflows/publish.yaml"

  # Generate atlan.yaml from template
  sed -e "s/{{NAME}}/$APP_NAME/g" -e "s/{{TYPE}}/$APP_TYPE/g" "$ATLAN_YAML_TEMPLATE" > "$APP_DIR/atlan.yaml"

  UPDATED=$((UPDATED + 1))
  echo "  ✓ build-image.yaml, publish.yaml, atlan.yaml"
done

echo ""
echo "Updated $UPDATED app(s)"

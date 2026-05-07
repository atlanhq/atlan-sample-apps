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
#
# Per-app overrides (optional atlan-scaffold-overrides.json alongside the registry):
#   execution_mode       — overrides the template default (e.g. "native")
#   split_deployment     — set to true to add splitDeploymentEnabled: true

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
  APP_NAME=$(basename "$APP_DIR")

  REL_PATH="${APP_DIR#"$REPO_ROOT/"}"

  # Derive app type from top-level directory
  TOP_DIR=$(echo "$REL_PATH" | cut -d'/' -f1)
  case "$TOP_DIR" in
    connectors) APP_TYPE="connector" ;;
    utilities)  APP_TYPE="utility" ;;
    *)          APP_TYPE="connector" ;;
  esac

  # Read optional per-app overrides from atlan-scaffold-overrides.json (requires python3)
  OVERRIDES_FILE="$APP_DIR/atlan-scaffold-overrides.json"
  EXEC_MODE=$(python3 -c "
import json, sys
try:
    d = json.load(open('$OVERRIDES_FILE'))
    print(d.get('execution_mode', ''))
except FileNotFoundError:
    print('')
" 2>/dev/null || true)

  SPLIT_DEPLOY=$(python3 -c "
import json, sys
try:
    d = json.load(open('$OVERRIDES_FILE'))
    print('true' if d.get('split_deployment') else '')
except FileNotFoundError:
    print('')
" 2>/dev/null || true)

  echo "Processing: $REL_PATH ($APP_NAME, type=$APP_TYPE)"

  # Copy workflow files
  mkdir -p "$APP_DIR/.github/workflows"
  cp "$WORKFLOW_SRC/build-image.yaml" "$APP_DIR/.github/workflows/build-image.yaml"
  cp "$WORKFLOW_SRC/publish.yaml" "$APP_DIR/.github/workflows/publish.yaml"

  # Generate atlan.yaml from template, applying per-app overrides via Python
  python3 - "$ATLAN_YAML_TEMPLATE" "$APP_DIR/atlan.yaml" "$APP_NAME" "$APP_TYPE" "$EXEC_MODE" "$SPLIT_DEPLOY" <<'PYEOF'
import sys

template_path, out_path, name, app_type, exec_mode, split_deploy = sys.argv[1:]

with open(template_path) as f:
    content = f.read()

content = content.replace("{{NAME}}", name).replace("{{TYPE}}", app_type)

if exec_mode:
    lines = content.splitlines(keepends=True)
    result = []
    for line in lines:
        if line.startswith("execution_mode:"):
            result.append(f"execution_mode: {exec_mode}\n")
            if split_deploy == "true":
                result.append("splitDeploymentEnabled: true\n")
        else:
            result.append(line)
    content = "".join(result)

with open(out_path, "w") as f:
    f.write(content)
PYEOF

  UPDATED=$((UPDATED + 1))
  echo "  ✓ build-image.yaml, publish.yaml, atlan.yaml"
done

echo ""
echo "Updated $UPDATED app(s)"

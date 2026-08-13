#!/usr/bin/env bash
set -euo pipefail

readonly REPO="/home/ubuntu/projects/holy-grail"
readonly STATE_DIR="/home/ubuntu/.local/state/holy-grail"

/usr/bin/mkdir -p "$STATE_DIR"
exec 9>"$STATE_DIR/regional-sync.lock"
/usr/bin/flock -n 9 || exit 0

cd "$REPO"
if [[ -n "$(/usr/bin/git status --porcelain)" ]]; then
  echo "regional sync skipped: repository has uncommitted changes" >&2
  exit 1
fi

/usr/bin/git pull --ff-only --quiet origin main
/usr/bin/python3 scripts/sync_regional_compute.py

if /usr/bin/git diff --quiet -- docs/regional_data.js docs/index.html; then
  exit 0
fi

/usr/bin/git add docs/regional_data.js docs/index.html
/usr/bin/git commit -m "Auto-sync regional compute data"
/usr/bin/git push --quiet origin main

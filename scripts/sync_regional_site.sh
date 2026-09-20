#!/usr/bin/env bash
set -euo pipefail

readonly REPO="/home/ubuntu/projects/holy-grail"
readonly STATE_DIR="/home/ubuntu/.local/state/holy-grail"

/usr/bin/mkdir -p "$STATE_DIR"
exec 9>"$STATE_DIR/regional-sync.lock"
/usr/bin/flock -n 9 || exit 0

cd "$REPO"
# The Python runner shares the publication lock with the labs publisher and
# stages only the audited encrypted build. This lock suppresses duplicate cron
# invocations of this wrapper; it is distinct from the shared publication lock.
exec /usr/bin/python3 scripts/publish_site.py regional

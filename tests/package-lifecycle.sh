#!/bin/bash
set -euo pipefail
major=$1
test "$(stat -c %a /etc/dockyard/session.key)" == 640
test "$(stat -c %a /etc/dockyard/auth.json)" == 640
test "$(stat -c %a /var/lib/dockyard/config)" == 700
sha256sum /etc/dockyard/session.key /etc/dockyard/auth.json /var/lib/dockyard/admin.password > /tmp/dockyard-before.sha256
rpm -Uvh --replacepkgs "/src/releases/1.0.0/el$major/rpms/dockyard-1.0.0-1.el$major.x86_64.rpm"
sha256sum --check /tmp/dockyard-before.sha256
runuser -u dockyard -- env DOCKYARD_DIR=/var/lib/dockyard DOCKYARD_CONFIG=/etc/dockyard PYTHONPATH=/opt/dockyard/web /opt/dockyard/venv/bin/gunicorn --workers 1 --threads 2 --bind 127.0.0.1:8080 app:app > /tmp/dockyard-live.log 2>&1 &
pid=$!
trap 'kill "$pid" 2>/dev/null || true' EXIT
for attempt in {1..20}; do
  if curl -fsS http://127.0.0.1:8080/healthz > /tmp/health.json; then break; fi
  sleep 0.5
done
grep -q Dockyard /tmp/health.json
test "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/api/settings)" == 401
kill "$pid" 2>/dev/null || true
wait "$pid" || true
trap - EXIT
rpm -e dockyard
sha256sum --check /tmp/dockyard-before.sha256
echo 'PASS: configuration permissions, reinstall preservation, unprivileged server, anonymous denial and uninstall retention'

#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
major=$1
engine=${CONTAINER_ENGINE:-podman}
"$engine" run --rm --network none --security-opt label=disable -v "$PWD:/src:ro" "docker.io/rockylinux/rockylinux:$major" bash -c "cd /src/releases/1.0.0/el$major && bash install.sh && runuser -u dockyard -- env DOCKYARD_TEST_INSTALLED=1 /opt/dockyard/venv/bin/python -m unittest discover -s /src/tests -v && bash /src/tests/package-lifecycle.sh $major"

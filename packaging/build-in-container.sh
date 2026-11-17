#!/bin/bash
set -euo pipefail
major=$1
dnf -y install rpm-build python3 python3-pip python3-devel gcc binutils make perl xz-devel openldap-devel cyrus-sasl-devel openssl-devel dnf-plugins-core createrepo_c tar gzip bsdtar
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
source="$work/dockyard-1.0.0"
mkdir -p "$source"
for item in web scripts profiles docs packaging tests .github .gitignore build.sh install.sh README.md HELP.md RELEASE_NOTES.md THIRD_PARTY_NOTICES.md; do cp -a "/src/$item" "$source/"; done
find "$source" -name __pycache__ -type d -prune -exec rm -rf {} +
python3 -m venv "$work/buildenv"
pip="$work/buildenv/bin/pip"
"$pip" install --upgrade pip wheel setuptools
mkdir "$source/wheels"
"$pip" wheel --wheel-dir "$source/wheels" -r /src/packaging/requirements.txt
python3 -m venv "$work/verify"
"$work/verify/bin/pip" install --no-index --find-links="$source/wheels" -r /src/packaging/requirements.txt
"$work/verify/bin/pip" check
"$work/verify/bin/pip" freeze > "$source/requirements.lock"
cd "$source"
"$work/verify/bin/pip" install pycdlib
"$work/verify/bin/python" scripts/make-test-iso.py
mkdir -p /src/tests/fixtures
cp tests/fixtures/boot-smoke.iso /src/tests/fixtures/
"$work/verify/bin/python" -m unittest discover -s tests -v
ipxe_commit=$(cat /src/packaging/IPXE_COMMIT)
curl --fail --location --retry 3 "https://api.github.com/repos/ipxe/ipxe/tarball/$ipxe_commit" -o "$source/ipxe-source.tar.gz"
mkdir "$work/ipxe"
tar -xzf "$source/ipxe-source.tar.gz" -C "$work/ipxe" --strip-components=1
make -C "$work/ipxe/src" -j2 bin/undionly.kpxe bin-x86_64-efi/ipxe.efi
mkdir "$source/ipxe"
cp "$work/ipxe/src/bin/undionly.kpxe" "$source/ipxe/"
cp "$work/ipxe/src/bin-x86_64-efi/ipxe.efi" "$source/ipxe/"
cp "$work/ipxe/COPYING" "$source/ipxe/COPYING"
python3 - "$source/ipxe/ipxe.efi" <<'PY'
from pathlib import Path
import sys
data=Path(sys.argv[1]).read_bytes()
assert data.startswith(b'MZ') and len(data)>100000, 'Invalid UEFI firmware'
PY
release="/src/releases/1.0.0/el$major"
mkdir -p "$release/rpms/dependencies" "$release/python-sources"
python3 /src/packaging/collect-sources.py "$source/requirements.lock" "$release/python-sources"
top="$work/rpmbuild"
mkdir -p "$top"/{SOURCES,SPECS,BUILD,BUILDROOT,RPMS,SRPMS}
tar -C "$work" -czf "$top/SOURCES/dockyard-1.0.0.tar.gz" dockyard-1.0.0
rpmbuild -bb --define "_topdir $top" --define "dist .el$major" "$source/packaging/dockyard.spec"
cp "$top"/RPMS/x86_64/*.rpm "$release/rpms/"
dnf download -y --resolve --alldeps --destdir "$release/rpms/dependencies" python3 python3-pip openldap bsdtar nginx dnsmasq systemd util-linux shadow-utils rpm-plugin-syslog policycoreutils-python-utils
createrepo_c "$release/rpms/dependencies"
cp /src/install.sh "$release/"
cp /src/docs/INSTALL.md "$release/INSTALL.md"
cp /src/RELEASE_NOTES.md "$release/RELEASE_NOTES.md"
cp "$source/requirements.lock" "$release/requirements.lock"
cp "$top/SOURCES/dockyard-1.0.0.tar.gz" "/src/releases/1.0.0/dockyard-1.0.0-el$major-source.tar.gz"
(cd "$release"; find rpms -type f -print0 | sort -z | xargs -0 sha256sum; sha256sum install.sh INSTALL.md RELEASE_NOTES.md requirements.lock) > "$release/SHA256SUMS"
tar -C "$release" -czf "/src/releases/1.0.0/dockyard-1.0.0-el$major-python-sources.tar.gz" python-sources
tar -C "$release" --exclude=python-sources -czf "/src/releases/1.0.0/dockyard-1.0.0-el$major-x86_64-offline.tar.gz" .

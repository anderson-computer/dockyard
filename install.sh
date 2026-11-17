#!/bin/bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Run sudo bash install.sh' >&2; exit 1; }
cd -- "$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")"
source /etc/os-release
major=${VERSION_ID%%.*}
[[ ${ID:-} == rocky && ( $major == 9 || $major == 10 ) && $(uname -m) == x86_64 ]] || { echo 'Use the matching Rocky Linux 9/10 x86_64 bundle.' >&2; exit 1; }
sha256sum --check --strict SHA256SUMS
shopt -s nullglob
app=(rpms/dockyard-*.el"$major".x86_64.rpm)
[[ ${#app[@]} == 1 && -f rpms/dependencies/repodata/repomd.xml ]] || { echo 'Wrong OS or incomplete release bundle.' >&2; exit 1; }
dnf -y --disablerepo='*' --repofrompath="dockyard-offline,file://$PWD/rpms/dependencies" --enablerepo=dockyard-offline --setopt=dockyard-offline.gpgcheck=1 --setopt=dockyard-offline.gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-Rocky-$major --setopt=install_weak_deps=False install "${app[@]}"
/opt/dockyard/venv/bin/pip check
dockyard version
echo 'Installed. No DHCP, TFTP or HTTP boot service has been activated. Follow INSTALL.md.'

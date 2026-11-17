%global debug_package %{nil}
%global __os_install_post %{nil}
Name: dockyard
Version: 1.0.0
Release: 1%{?dist}
Summary: Dockyard PXE network boot and provisioning server
License: LicenseRef-Proprietary AND GPL-2.0-or-later AND BSD-2-Clause AND MIT
URL: https://github.com/mike0615/lrn-pxe
Source0: dockyard-1.0.0.tar.gz
BuildArch: x86_64
Requires: python3
Requires: python3-pip
Requires: openldap
Requires: bsdtar
Requires: nginx
Requires: dnsmasq
Requires: systemd
Requires: util-linux
Requires(pre): shadow-utils

%description
Dockyard manages ISO images, kickstart files and BIOS/UEFI iPXE menus through
an authenticated loopback web interface. Runtime dependencies and iPXE firmware
are bundled. Network services require explicit administrator configuration.

%prep
%setup -q

%build
test -s requirements.lock
test -s ipxe/ipxe.efi

%install
install -d %{buildroot}/opt/dockyard
cp -a web scripts profiles docs wheels requirements.lock ipxe ipxe-source.tar.gz HELP.md README.md RELEASE_NOTES.md THIRD_PARTY_NOTICES.md %{buildroot}/opt/dockyard/
install -m 0755 packaging/setup-runtime.sh %{buildroot}/opt/dockyard/setup-runtime.sh
install -D -m 0755 packaging/dockyard %{buildroot}/usr/bin/dockyard
install -D -m 0644 packaging/dockyard.service %{buildroot}/usr/lib/systemd/system/dockyard.service
install -D -m 0644 packaging/dockyard-dnsmasq.service %{buildroot}/usr/lib/systemd/system/dockyard-dnsmasq.service
find %{buildroot}/opt/dockyard -type f -exec chmod 0644 {} +
chmod 0755 %{buildroot}/opt/dockyard/setup-runtime.sh

%pre
getent group dockyard >/dev/null || groupadd -r dockyard
getent passwd dockyard >/dev/null || useradd -r -g dockyard -d /var/lib/dockyard -s /sbin/nologin dockyard

%post
/opt/dockyard/setup-runtime.sh || exit 1
systemctl daemon-reload >/dev/null 2>&1 || :

%preun
if [ "$1" -eq 0 ]; then systemctl disable --now dockyard dockyard-dnsmasq >/dev/null 2>&1 || :; fi

%postun
systemctl daemon-reload >/dev/null 2>&1 || :
if [ "$1" -ge 1 ]; then systemctl try-restart dockyard >/dev/null 2>&1 || :; fi

%files
/opt/dockyard/
/usr/bin/dockyard
/usr/lib/systemd/system/dockyard.service
/usr/lib/systemd/system/dockyard-dnsmasq.service

%changelog
* Tue Nov 17 2026 Mike Anderson <mike@andersoncomputer.us> - 1.0.0-1
- Rename LRN-PXE as Dockyard; authenticated management, TLS LDAP and safe file boundaries
- Bundle offline runtime and pinned BIOS/UEFI iPXE firmware; explicit network activation

# Dockyard

PXE network boot and provisioning management for Rocky Linux 9 and 10.
Formerly LRN-PXE. Author: Mike Anderson. Version 1.0.0.

Dockyard provides authenticated ISO management, userspace ISO extraction,
kickstart editing and BIOS/UEFI iPXE menu generation. The management service
runs without root privileges and listens on loopback. DHCP/TFTP and boot HTTP
are configured and activated explicitly by a server administrator.

## Install

Use the complete Rocky 9 or 10 x86_64 offline bundle from the repository's
Releases page. Extract into a new directory and run `sudo bash install.sh`.
Read `/var/lib/dockyard/admin.password` privately as root, then enable the
management app with `sudo systemctl enable --now dockyard`. Open
http://127.0.0.1:8080 on the server, or use an SSH tunnel.

Installation does not activate DHCP, TFTP or boot HTTP and does not overwrite
existing dnsmasq/nginx configurations. See [installation](docs/INSTALL.md) before
activating provisioning on an authorized isolated network. ISO files and client
operating-system licenses are supplied by the operator.

## Documentation

- [Embedded help](HELP.md), available in-app with F1
- [Installation and network activation](docs/INSTALL.md)
- [Code review and validation](docs/CODE_REVIEW.md)
- [Migration from LRN-PXE](docs/MIGRATION.md)
- [Release notes](RELEASE_NOTES.md)
- [Technical specification](docs/SPEC_SHEET.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

See the [operator guide](docs/USER_GUIDE.md), [ICD](docs/ICD.md),
[offline build guide](docs/AIRGAP_INSTALL.md) and
[identity guide](docs/FREEIPA_AUTHENTICATION.md) for additional detail.

## Build

`bash build.sh 9 10` uses Podman, or set `CONTAINER_ENGINE=docker`. A connected
build host prepares matching wheels, signed OS dependency repositories and
iPXE firmware from the pinned source revision. Target installs never contact
online repositories. See `packaging/IPXE_COMMIT` for the iPXE revision; its full
source archive is included with the application. Physical BIOS/UEFI and site
LDAP/SELinux qualification remain deployment checks. RPMs are unsigned.

Dockyard is released under the MIT License (see `LICENSE`). Third-party
components retain their own licenses; see `THIRD_PARTY_NOTICES.md`.

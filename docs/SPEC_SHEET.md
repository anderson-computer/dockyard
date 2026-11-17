# Dockyard 1.0.0 specifications

Self-hosted ISO, kickstart and iPXE management for Rocky Linux 9/10 x86_64.
Cyber Chief toolkit member; application name is Dockyard.

| Item | Specification |
|---|---|
| Delivery | Native EL9/EL10 RPMs, offline bundles, SHA256 manifests, source archives |
| Runtime | Distribution Python, private offline venv, Flask/Gunicorn, python-ldap |
| Management | Loopback TCP 8080; SSH tunnel or site-managed HTTPS proxy |
| Provisioning | TCP 8081 HTTP; UDP 69 TFTP; optional UDP 67 DHCP |
| Firmware | BIOS undionly.kpxe and x86_64 UEFI ipxe.efi; pinned source included |
| Services | Unprivileged dockyard; optional dockyard-dnsmasq and nginx |
| State | /var/lib/dockyard; root-managed /etc/dockyard configuration |
| Identity | Local hashed password; optional verified LDAP TLS and admin group |
| Help | Embedded /help, /about and F1; local Bootstrap assets |
| Capacity | Up to 500 menu entries; 50 GB suggested disk, image-dependent |

Management covers ISO upload/delete/extract, kickstart upload/edit/delete, menu
editing/reordering, settings and status. Privileged network configuration and
service activation require the server administrator CLI. Installation does not
start DHCP or boot HTTP automatically. Application RPMs and firmware are unsigned.

Physical BIOS/UEFI boot, Secure Boot, production LDAP, site ISO arguments and
SELinux enforcing behavior require site qualification. Container tests do not
establish those results. See CODE_REVIEW.md and RELEASE_NOTES.md.

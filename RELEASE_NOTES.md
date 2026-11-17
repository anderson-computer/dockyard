# Dockyard 1.0.0 — November 17, 2026

First Dockyard release, renamed from LRN-PXE.

- Adds working local administrator login, protected management APIs, CSRF/origin
  checks, login throttling, persistent session signing and session revocation.
- Runs management as an unprivileged service; removes privileged web restarts
  and root loop mounts. ISO contents are extracted using libarchive/bsdtar.
- Rejects unsafe filenames, symlink escapes, menu control characters and unknown
  authentication settings submitted through the provisioning API.
- Fixes menu-control HTML escaping and unsafe toast rendering.
- Requires verified TLS for LDAP authentication and the configured admin group.
- Removes weak template passwords, automatic menu activation and CDN fallbacks.
- Provides embedded Help/About, offline RPM installers for Rocky 9/10, checksum
  manifests, source archives and pinned BIOS/UEFI iPXE firmware with source.

DHCP/TFTP and boot HTTP require explicit administrator configuration and activation.
No production network was modified by release testing. Physical BIOS/UEFI boot,
site-specific operating-system images, LDAP CA/group integration and SELinux
enforcing behavior remain deployment qualification checks. Existing LRN-PXE
state is migrated explicitly; no automatic destructive conversion is performed.
RPMs are unsigned. Source ownership and third-party licensing remain as documented.

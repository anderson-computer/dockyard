# Dockyard code review and release validation

The review found and corrected these release blockers:

| Finding | Correction |
|---|---|
| Unauthenticated root management API | Login, CSRF/origin guards and unprivileged service |
| Plain LDAP password binding | Verified TLS before bind, escaped DN/filter values and administrator-group check |
| Upload/path traversal and symlink escapes | Strict resource names, confined paths and regression tests |
| Broken ISO-copy fallback and privileged mounts | Real userspace ISO extraction with libarchive |
| Menu HTML injection and unsafe toast content | JSON/attribute escaping and text-safe toast values |
| Weak provisioning template passwords | Locked/unconfigured accounts until operator supplies approved credentials |
| GET polling silently enabled boot entries | Read-only status; explicit operator enable |
| CDN fallbacks broke air-gap assumptions | Local bundled assets only |
| Installer started network services automatically | Explicit configuration and activation |

The automated suite covers login/session/CSRF boundaries, path and symlink
rejection, menu validation and escaping, unprivileged service boundaries,
actual synthetic ISO extraction, offline help/assets, LDAP TLS ordering and
session revocation. Native packaging and network-disabled install tests run for
Rocky Linux 9 and 10, including private configuration modes, reinstall persistence
and removal retention. These tests do not boot a physical client or validate a
site's DHCP, LDAP directory, image license or SELinux policy.

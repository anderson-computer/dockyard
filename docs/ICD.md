# Dockyard 1.0.0 interface control document

## Management boundary
Management listens on 127.0.0.1:8080. POST /login accepts username, password and
the CSRF form token. Sessions expire after 30 minutes and use HttpOnly and
SameSite=Strict cookies. Enable Secure cookies for an HTTPS-only proxy.
Management APIs require login; mutations require the session CSRF token in
X-CSRF-Token or csrf_token and a same-origin request. Anonymous APIs return 401.
Service restart requests return 409 with a server-administrator instruction.

| Endpoint | Methods | Function |
|---|---|---|
| /healthz | GET | Public readiness identity |
| /menu.ipxe | GET | Public plain-text iPXE script |
| /help, /about | GET | Embedded documentation |
| /login, /logout | GET/POST, POST | Session lifecycle |
| /api/images | GET | Image inventory |
| /api/images/upload | POST | Multipart ISO upload |
| /api/images/{id} | DELETE | Remove image |
| /api/images/{id}/extract | POST | Begin extraction |
| /api/images/{id}/extract/status | GET | Read-only progress |
| /api/kickstarts | GET | Kickstart inventory |
| /api/kickstarts/upload | POST | Multipart upload |
| /api/kickstarts/{name} | GET/PUT/DELETE | Read/edit/remove |
| /api/menu | GET/PUT | Read/replace validated JSON menu |
| /api/menu/entries | POST | Add entry |
| /api/menu/entries/{id} | PUT/DELETE | Edit/remove entry |
| /api/menu/reorder | POST | Reorder entries |
| /api/settings | GET/PUT | Whitelisted provisioning settings |
| /api/status | GET | Disk and service status |

This internal interface is versioned with the release. Request schemas are in
web/app.py and the bundled UI. Resource names permit ASCII letters, digits,
underscore, hyphen and single dots; traversal and symlink escapes are rejected.
Menu strings cannot contain control characters or newlines. Authentication
configuration cannot be written through the provisioning API.

## Provisioning and host interfaces
Dedicated dnsmasq distinguishes BIOS, x86_64 UEFI and iPXE clients. iPXE clients
receive http://SERVER:8081/menu.ipxe. nginx exposes that script plus boot, mounts,
isos and kickstarts content. Content on this network is public: keep secrets out
of published kickstarts. Existing DHCP needs equivalent architecture and iPXE
bootfile options. Network activation is explicit; see INSTALL.md.

Host configuration is /etc/dockyard/auth.json and session.key, root-managed and
readable only by root and the service group. Data is /var/lib/dockyard. CLI commands
are version, status, admin-password and configure-network. Password rotation
revokes sessions. Optional LDAP uses verified StartTLS or LDAPS and checks the
administrator group; provisioning settings hold no directory administrator secret.
Backups must retain configuration and state consistently. Removal retains both.

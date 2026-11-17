# Dockyard help

Dockyard manages network boot images and configuration. Log in using the local
administrator account or an explicitly configured FreeIPA administrator group.
The initial local username is admin; read its generated password privately on
the server. Change it using `sudo dockyard admin-password`. Password changes
revoke existing management sessions.

## Images and menus

Upload a reviewed ISO with a simple filename. Extract its boot files, then
review the generated menu entry and explicitly enable it in Menu Builder.
Extraction uses bsdtar without mount/root privileges and retains the extracted
installation tree for HTTP boot. RHEL, Ubuntu and Debian images have different
boot layouts; verify kernel/initrd paths and OS-specific arguments before use.
Polling extraction status does not enable boot entries.

## Kickstarts

Create or upload a kickstart/configuration file and associate it with a menu
entry. Templates leave login accounts locked or unconfigured until you supply
your own approved password hashes or SSH keys. Boot files and kickstarts are
served without interactive authentication to PXE clients on the provisioning
network. Do not put reusable plaintext secrets into boot content.

## Network activation

The management app listens on 127.0.0.1:8080. Boot HTTP uses the explicitly
configured server address on port 8081. Generate configuration with
`sudo dockyard configure-network` and the required interface/server-IP options.
Omit DHCP pool arguments when retaining an existing DHCP server; configure its
boot options separately. Read INSTALL.md before activating any network services.
The web app never gains root privileges to restart services or mount images.

## Help, About and recovery

F1 opens local help; About shows name, version, author and component notices.
No CDN or internet connection is needed at runtime. Back up `/var/lib/dockyard`
and `/etc/dockyard` while the service is stopped, preserving permissions. An
uninstall retains operational data and generated keys. Use journalctl for the
management service and the dedicated network service. Legacy LRN-PXE migration
is explicit; existing services and state are not automatically replaced.

# Dockyard installation and activation

Use the complete release bundle for your Rocky Linux major version (9 or 10),
x86_64. Plan for a static server address and at least 50 GB storage for real ISOs.
Extract into an empty directory, verify SHA256SUMS against trusted release media,
then run `sudo bash install.sh`. Application RPMs are unsigned; bundled OS
dependency RPMs retain their distribution signatures. No repository outside the
local bundle is enabled during installation.

## Management app

Read `/var/lib/dockyard/admin.password` privately as root. The initial username
is admin; neither the installer nor logs print the password. Run
`sudo systemctl enable --now dockyard`, then open http://127.0.0.1:8080 locally.
For a remote workstation use `ssh -L 8080:127.0.0.1:8080 user@server`, keeping the
tunnel open. Change the bootstrap password with `sudo dockyard admin-password`.
Keep administration on the SSH tunnel or configure a trusted internal HTTPS
proxy that consistently forwards the original Host header. Set DOCKYARD_HTTPS=true
in a systemd override when using HTTPS exclusively so session cookies are Secure.

## Boot network configuration — explicit server-side step

Run `sudo dockyard configure-network --interface INTERFACE --server-ip ADDRESS`.
This generates TFTP-only configuration for use with an existing DHCP server.
Configure that server's next-server/bootfile options for the Dockyard TFTP server;
iPXE clients must receive the HTTP menu URL. Use the generated dnsmasq config as
the reference for BIOS versus UEFI and iPXE chainload options.

For a dedicated DHCP segment, also supply `--dhcp-start`, `--dhcp-end`,
`--netmask`, `--gateway` and `--dns`. The pool must be on the server subnet and
must exclude the server address. Review the generated files before activation.
Do not activate a second DHCP server on a segment managed by another DHCP server.

Review `/etc/dockyard/dnsmasq.conf` and `/etc/dockyard/dockyard-boot.nginx`.
After review, copy the nginx file to `/etc/nginx/conf.d/dockyard-boot.conf`, run
`sudo nginx -t`, and enable/reload nginx as appropriate. Enable the dedicated
`dockyard-dnsmasq` unit only on the selected provisioning network. The package
never overwrites the system dnsmasq configuration. Allow only the necessary
provisioning interfaces/clients through firewall rules: UDP 69 for TFTP, UDP 67
when serving DHCP, and TCP 8081 for boot HTTP. Management port 8080 stays local.

On SELinux enforcing systems, apply reviewed HTTP file contexts to the ISO,
boot, mounts and kickstarts directories and an appropriate TFTP context to the
TFTP directory. Verify the port context for 8081. Do not disable SELinux to make
the app work. Site SELinux policy verification is a release qualification step.

## Identity integration

Local authentication works without LDAP. Configure optional `ldap_enabled`,
`ldap_server`, `ldap_base_dn` and `ldap_admin_group` in root-managed
`/etc/dockyard/auth.json`, retaining the local password_hash and username fields.
Use a trusted internal CA. ldap:// is upgraded with StartTLS before password
binding; ldaps:// uses TLS immediately. Certificate validation remains required.
The authenticating account must be in the configured administrator group.
No directory administrator bind password is stored in provisioning settings.

## Upgrade, backup and removal

Back up `/var/lib/dockyard` and `/etc/dockyard` consistently while stopped. Protect
session keys, password hashes and kickstart content in encrypted backups. RPM
reinstall preserves data and generated configuration. Uninstall removes the app
and service units and retains data/configuration for deliberate recovery. Undo
any nginx configuration enabled manually before removing the provisioning service.
See MIGRATION.md for an existing LRN-PXE deployment. PXE physical boot testing
and image-specific arguments must be verified on your hardware before deployment.

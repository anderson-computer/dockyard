# Dockyard identity integration

The local administrator works without FreeIPA. Configure optional LDAP only in
root-managed /etc/dockyard/auth.json, retaining username, password_hash and
auth_revision. Set ldap_enabled to true, ldap_server to ldap://ipa.example.internal
or ldaps://ipa.example.internal, ldap_base_dn to your directory base and
ldap_admin_group to the exact required group name. Accounts are looked up under
uid=USERNAME,cn=users,cn=accounts,BASE_DN and must list that group in memberOf.

Install the internal CA into system trust first. ldap:// requires verified
StartTLS before binding; ldaps:// starts TLS immediately. There is no plaintext
bind fallback. No directory administrator DN/password is required or stored.
Authentication settings cannot be changed through the provisioning settings API.

Restart dockyard after root configuration changes. Test a permitted account, a
nonmember and an invalid CA against a staging directory. Container tests exercise
the TLS-before-bind and group-check code with mocks; a production directory was
not used for release qualification. Retain local access for recovery using
sudo dockyard admin-password. Do not disable authentication or certificate checks.
See INSTALL.md for SSH tunnel/HTTPS, cookie settings and backup requirements.

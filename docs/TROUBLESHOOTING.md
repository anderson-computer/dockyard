# Dockyard troubleshooting

- Management unavailable: inspect systemctl status dockyard and journalctl -u
  dockyard, loopback 8080 and the SSH tunnel. Change the workstation forwarded port
  if occupied while retaining remote 8080.
- Login fails: sudo dockyard admin-password resets the local password. LDAP requires
  trusted CA, connectivity and exact administrator-group membership. Repeated
  attempts are throttled. Keep certificate validation enabled.
- Mutation rejected: sign in again to refresh session/CSRF. HTTPS proxies must
  preserve the original Host header.
- Extraction fails: inspect permissions, storage and journal output. Use a valid
  ISO and safe filename; extraction runs without root mounts.
- PXE fails: verify approved DHCP, architecture bootfile, TFTP and HTTP 8081.
  Avoid competing DHCP servers; qualify Secure Boot separately (unsigned firmware).
- Boot HTTP denied: review nginx, firewall and SELinux file/port policies using
  INSTALL.md. Do not disable enforcement as a workaround.
- Restart button gives instructions: intentional; restart from an authorized server
  shell. DHCP/TFTP uses dockyard-dnsmasq, not the system-wide dnsmasq configuration.

Container validation does not qualify physical firmware, production DHCP/LDAP,
site images or SELinux enforcing behavior. See CODE_REVIEW.md.

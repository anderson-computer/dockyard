# Migrating LRN-PXE to Dockyard

Back up the existing application, ISOs, extracted trees, boot files, kickstarts,
configuration, systemd units and dnsmasq/nginx files. Stop the old management
service and disable its network services only during an approved maintenance
window. Dockyard does not automatically stop or erase an existing deployment.

Install Dockyard with its matching offline bundle and leave network services
inactive. Copy reviewed ISOs, kickstarts and extracted trees into their matching
directories under `/var/lib/dockyard`, preserving expected simple filenames.
Restore ownership to dockyard:dockyard, directories to 0755 and boot content to
0644. The `config` directory must remain 0700 and its JSON files 0600.

Review menu JSON before importing it. Entry IDs, ISO names and kickstart names
must pass the stricter resource-name validation. Remove control characters and
check every kernel argument. Rename or rewrite legacy entries as needed.
Do not copy LDAP passwords into provisioning settings. Configure LDAP through the
new root-managed auth file and verify local login before enabling directory login.

Generate fresh network configuration, compare it with the original DHCP/proxy
settings and test on an isolated segment. Existing root loop mounts are not
adopted; extract clean trees using Dockyard. Test BIOS/UEFI, repository URLs and
kickstart access before switching production boot options. Keep the old backup
and configuration through the rollback period. Never run competing DHCP servers.

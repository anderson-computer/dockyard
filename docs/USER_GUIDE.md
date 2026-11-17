# Dockyard operator guide

Follow INSTALL.md to install, activate management and rotate the generated admin
password. Access management locally or through the documented SSH tunnel. Help
and F1 provide embedded instructions; About identifies the release.

1. Generate network configuration with the root CLI, review and activate explicitly.
2. In Boot Images, upload a licensed ISO with a simple safe filename.
3. Extract boot files and wait for completion. Extraction does not enable entries.
4. Create/upload a kickstart if needed. Sample accounts are locked until configured.
   Published kickstarts are network-readable; avoid embedding secrets.
5. Add/edit a Menu Builder entry, kernel arguments and kickstart, then enable it
   deliberately. Inspect View iPXE Menu before booting a client.
6. Test your images and BIOS/UEFI clients on the approved provisioning segment.

UI settings store metadata; they do not apply privileged service configuration.
Use an authorized server shell for service operations. Back up content before
deleting resources. Preserve /etc/dockyard and /var/lib/dockyard in protected backups.
See INSTALL.md, MIGRATION.md and CODE_REVIEW.md for deployment requirements and gaps.

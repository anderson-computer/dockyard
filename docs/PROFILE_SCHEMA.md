# LRN PXE Profile and Capability Schema

This document defines the profile model that `lrn-pxe` should use when generating
menu entries and unattended install manifests.

## Design goals

- Keep the number of boot images small.
- Separate base OS installation from post-install orchestration.
- Allow one profile to compose multiple capabilities.
- Keep room for Rocky 9.x and Rocky 10.x variants.
- Support future UI-driven menu generation without changing the manifest format.

## Model

A PXE install request is composed of:

- one `os_release`
- one `profile`
- zero or more `capabilities`
- one `identity` block
- one `network` block
- one `bootstrap` block

The PXE layer should generate a node manifest at install time and hand it to the
firstboot bootstrap. The bootstrap then executes the matching `lrn-ansible`
profile playbook and any selected capability playbooks.

## Manifest schema

```json
{
  "schema_version": "1.0",
  "os_release": "rocky-9.7",
  "profile": "server-core",
  "capabilities": [
    "join-freeipa-client",
    "register-dns",
    "service-openfire"
  ],
  "identity": {
    "hostname": "openfire-01",
    "fqdn": "openfire-01.acc.local",
    "site": "primary",
    "environment": "production"
  },
  "network": {
    "bootproto": "dhcp",
    "ip_address": "",
    "prefix": "",
    "gateway": "",
    "dns_servers": ["192.168.64.1"]
  },
  "freeipa": {
    "realm": "ACC.LOCAL",
    "domain": "acc.local",
    "server": "ipa01.acc.local",
    "enroll": true,
    "otp": ""
  },
  "dns": {
    "register": true,
    "zone": "acc.local",
    "ttl": 3600,
    "provider": "freeipa"
  },
  "bootstrap": {
    "ansible_repo": "/opt/lrn-ansible",
    "manifest_path": "/etc/lrn/node-manifest.json",
    "run_mode": "firstboot",
    "ansible_source": "file:///usr/local/share/lrn-ansible"
  }
}
```

## Required fields

- `schema_version`
- `os_release`
- `profile`
- `identity.hostname`
- `identity.fqdn`
- `bootstrap.ansible_repo`
- `bootstrap.manifest_path`

## Profile rules

Profiles represent the base purpose of the node. They should stay coarse.

Recommended starter profiles:

- `server-core`
- `workstation-admin`
- `freeipa-server`
- `freeipa-replica`
- `dns-server`
- `openfire-server`
- `webapps-server`

Rules:

- A profile may declare default capabilities.
- A profile should not hardcode application secrets.
- A profile should remain valid across Rocky point releases where possible.
- A profile should be installable from a shared base ISO.

## Capability rules

Capabilities are additive behaviors layered on top of a profile.

Recommended starter capabilities:

- `join-freeipa-client`
- `register-dns`
- `monitoring-librenms-client`
- `service-openfire`
- `service-wikijs`
- `service-netbox`
- `service-guacamole`

Rules:

- Capabilities must be independently testable.
- Capabilities should declare ordering requirements.
- Capabilities may require profile guardrails.
- Capabilities should avoid duplicating baseline OS configuration.

## Menu generation guidance

`lrn-pxe` should present menu choices as profile-driven presets, not as a flat list
of low-level toggles.

Recommended first-layer menu examples:

- `Rocky 9.7 Interactive`
- `Rocky 9.7 Server Core`
- `Rocky 9.7 FreeIPA Replica`
- `Rocky 9.7 DNS Server`
- `Rocky 9.7 Openfire Server`
- `Rocky 10.1 Server Core`
- `Rocky 10.1 Admin Workstation`

Each menu entry should map to:

- one shared ISO
- one generated kickstart
- one generated node manifest
- one `lrn-ansible` execution path

## Implementation notes

- Kickstart should stay focused on base install and bootstrap delivery.
- The manifest is the contract between PXE and `lrn-ansible`.
- FreeIPA server and FreeIPA replica should remain separate profiles.
- DNS registration and FreeIPA client enrollment should stay optional capabilities.

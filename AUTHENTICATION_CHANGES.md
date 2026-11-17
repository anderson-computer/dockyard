# Dockyard 1.0.0 authentication changes

The original authentication module was not wired into management requests. This
release installs a mandatory login/session boundary, CSRF and origin checks,
rate limits, local hashed credentials, and verified LDAP TLS/group authentication.
The unprivileged web service cannot edit root-managed authentication configuration.
Password rotation revokes existing management sessions. No authentication-off
deployment mode is provided. See docs/FREEIPA_AUTHENTICATION.md, docs/ICD.md and
docs/CODE_REVIEW.md for configuration, interfaces and validation limits.

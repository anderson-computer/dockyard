# Dockyard offline build and installation

On a connected build host with Podman (or CONTAINER_ENGINE=docker), run
bash build.sh 9 10. Each target is built inside matching Rocky Linux, including
Python wheels, dependency RPM closure, iPXE BIOS/UEFI firmware and upstream source.
Run bash packaging/test-offline.sh 9 and 10 for network-disabled installation and
lifecycle checks. GitHub's release workflow gates publication on both builds/tests.

Outputs are under releases/1.0.0. Transfer the correct EL9/EL10 x86_64 offline
archive and trusted SHA256SUMS to the target using approved media. Extract into a
fresh directory, validate checksums, then run sudo bash install.sh. Local DNF/pip
repositories are used exclusively; internet access is unnecessary. Python source
archives and application source archives are published alongside installers.

Application RPMs are unsigned; dependency RPMs retain distribution signatures.
Use trusted media to authenticate the manifest. INSTALL.md covers management
credentials, loopback access, explicit network configuration/activation, SELinux,
backup and removal. Do not mix dependency packages between Rocky major versions.

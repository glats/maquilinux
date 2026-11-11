# Local workflow references

- [Acceptance tests](../../../../agent_docs/acceptance-tests.md)
- [Multiarch guide](../../../../agent_docs/multiarch-guide.md)
- [CLI reference](../../../../agent_docs/mql-cli-reference.md)
- [Build workflow](../../../../agent_docs/build-workflow.md)

For claims beyond package acceptance, inspect only the relevant current path:

- [VM launcher](../../../../lib/vm.sh): distinguish launch from observed guest behavior.
- [Consumer repository configuration](../../../../SOURCES/maquilinux.repo): verify the actual consumer trust settings.
- [Rootfs provisioning](../../../../scripts/provision-rootfs.sh) and [local install path](../../../../scripts/install-spec.sh): distinguish bootstrap/local behavior from signed consumer installation.

# Tasks: Build Rust & rpm-sequoia Chain

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: not-applicable
400-line budget risk: Low

## Pre-Build Checks

- [ ] PRE-1: `df -h $MQL_LFS` -- verify Avail >25GB. Time: 1 min.
- [ ] PRE-2: `mql chroot --exec "echo ok"` -- chroot functional. Time: 1 min.
- [ ] PRE-3: `mql chroot --exec "gpg --list-secret-keys"` -- GPG key exists. **Decision**: create if missing. Time: 2 min.

## Stage 1: Crypto Dependencies (~25 min)

- [ ] C1: Fetch sources: `for s in nettle libgpg-error libgcrypt libassuan gpgme; do ./scripts/fetch-spec-sources.sh $s || exit 1; done`. Time: 5 min.
- [ ] C2: Build chain: `./scripts/build-chain.sh nettle,libgpg-error,libgcrypt,libassuan,gpgme --skip-tests`. Verify: 5 RPMs in RPMS/x86_64/. Time: 20 min. Depends: C1.
- [ ] C3: Verify in chroot: `mql chroot --exec "ldconfig -p | grep -E '(nettle|libgcrypt|libgpg-error|libassuan|gpgme)'"`. Time: 1 min. Depends: C2.

## Stage 2: Build Dependencies (~100 min)

- [ ] B1: Fetch: `for s in libssh2 llvm; do ./scripts/fetch-spec-sources.sh $s || exit 1; done`. Time: 5 min.
- [ ] B2: Build: `./scripts/build-chain.sh libssh2,llvm --skip-tests`. Verify: libssh2 + llvm RPMs in RPMS/x86_64/. Time: 90 min. Depends: B1, C2.
- [ ] B3: Verify: `mql chroot --exec "llvm-config --version"` -- returns version string. Time: 1 min. Depends: B2.

## Stage 3: Rust Toolchain (~4-6h, async)

- [ ] R1: Backup: `mql backup create pre-rust`. Verify: `mql backup list | grep pre-rust`. Time: 2 min.
- [ ] R2: Fetch: `./scripts/fetch-spec-sources.sh rust`. Verify: `ls SOURCES/rustc-*.tar.*`. Time: 5 min.
- [ ] R3: Build async: `./scripts/build-chain.sh rust --async --skip-tests`. Verify: `tmux list-sessions | grep build-rust`. **Decision**: confirm 4-6h window. Time: 30 sec.
- [ ] R4: Monitor: `./scripts/check-build-status.sh rust` until complete. Alternate: `tmux attach -t build-rust-*` or `tail -f logs/rust-async-*.log`. Time: 4-6h. Depends: R3.
- [ ] R5: Verify RPMs: `ls RPMS/x86_64/{rustc,cargo,rust-std,rust-toolchain}-*.rpm`. Time: 1 min. Depends: R4.
- [ ] R6: Verify chroot: `mql chroot --exec "rustc --version && cargo --version && ldconfig -p | grep nettle"`. Time: 1 min. Depends: R5.

## Stage 4: rpm-sequoia (~20 min)

- [ ] S1: Build: `./scripts/fetch-spec-sources.sh rpm-sequoia && ./scripts/build-chain.sh rpm-sequoia --skip-tests`. Verify: RPM in RPMS/x86_64/. Time: 15 min. Depends: R6.
- [ ] S2: Verify: `mql chroot --exec "ldconfig -p | grep rpm_sequoia && rpm -q --requires rpm-sequoia | grep cargo"`. Time: 1 min. Depends: S1.

## Stage 5: RPM Rebuild (~15 min)

- [ ] M1: Build: `./scripts/build-chain.sh rpm --skip-tests`. Verify: new `rpm-[0-9]*.rpm` in RPMS/x86_64/. Time: 10 min. Depends: S2.
- [ ] M2: Verify: `mql chroot --exec "rpm --showrc | grep -i sequoia"` -- sequoia flag present. Time: 1 min. Depends: M1.

## Stage 6: GPG Signing Test (~5 min)

- [ ] G1: Sign: `mql chroot --exec "rpm --define '_gpg_name Maqui Linux' --addsign /mnt/repo/nettle-*.rpm"`. Time: 2 min. Depends: M2, PRE-3.
- [ ] G2: Verify: `mql chroot --exec "rpm --checksig /mnt/repo/nettle-*.rpm"` -- output shows "digests signatures OK". Time: 1 min. Depends: G1.

## CI Integration (~10 min)

- [ ] CI-1: Add workflow_dispatch for rust-bootstrap chain in `.github/workflows/build-rpms.yml` with 600min timeout. **Decision**: split workflow or extend? Time: 10 min. Depends: G2.



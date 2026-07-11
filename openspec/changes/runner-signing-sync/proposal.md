# Proposal: Runner Registration + Production Signing + Repo Sync

## Intent

Three production gaps block reliable CI/CD: (1) the self-hosted runner dies on nightly reboots, (2) all 171 production RPMs are unsigned, and (3) repo sync requires manual sudo intervention. This change makes the runner persistent, signs the entire RPM catalog, and automates publishing.

## Scope

### In Scope
- Configure runner with NixOS library workarounds (LD_LIBRARY_PATH + DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1)
- Create systemd user service for runner auto-start after reboot
- Batch-sign all 171 existing RPMs on rog with new GPG key
- Regenerate repodata on rog with signed RPMs
- Fix rog directory permissions for CI rsync access
- Export and backup GPG secret key to encrypted store
- Update CI workflow to verify signed RPMs on sync

### Out of Scope
- Re-registering runner with GitHub (requires web UI token, manual step)
- Moving to cloud-hosted runner
- Re-signing with old key (RPMs were never signed)
- i686 RPM signing (deferred, only x86_64 in scope)

## Capabilities

### New Capabilities
- `runner-persistence`: systemd user service and wrapper script for GitHub Actions runner survival across reboots on NixOS
- `rpm-signing`: batch GPG signing workflow for existing and new RPMs using rpm-sequoia
- `repo-sync`: automated repository synchronization with proper permission handling for CI publishing

### Modified Capabilities
- None

## Approach

1. **Runner**: Consolidate existing LD_LIBRARY_PATH wrapper into a single script at `~/actions-runner/run.sh`, create `~/.config/systemd/user/github-runner.service` with `Restart=always` and `RestartSec=10`, enable with `loginctl enable-linger`
2. **Signing**: Export GPG secret key from thinkcentre to rog via encrypted transfer, batch-sign 171 RPMs in-place with `rpm --addsign`, regenerate repodata with `createrepo_c`, delete key from rog immediately after
3. **Repo sync**: Use passwordless sudo on rog for rsync and createrepo_c operations; update workflow to use `sudo` prefix for these commands
4. **Key backup**: Export secret key to `sops`-encrypted file in repo secrets directory

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `~/.config/systemd/user/github-runner.service` | New | systemd user service for runner persistence |
| `~/actions-runner/run.sh` | New | Consolidated wrapper with NixOS library workarounds |
| `rog:/srv/glats/nginx/repo/` | Modified | All 171 RPMs signed in-place, repodata regenerated |
| `rog:/srv/glats/nginx/repo/` permissions | Modified | Directory group or sudoers entry for rsync |
| `secrets/` (encrypted) | New | GPG secret key backup |
| `.github/workflows/build.yml` | Modified | Repo sync steps use sudo, verify signatures |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| GPG key exposure on rog during transfer | Low | Encrypted transfer only, immediate deletion after signing |
| Signing corrupts RPMs | Low | Test with 3 RPMs first, verify with `rpm --checksig` before bulk |
| systemd service fails on NixOS | Medium | Test service manually before enabling, keep manual fallback |
| repodata regeneration breaks repo | Low | Backup repodata/ before regeneration, verify with `dnf check-update` |

## Rollback Plan

1. **Runner**: `systemctl --user stop github-runner && systemctl --user disable github-runner` — revert to manual start
2. **Signing**: Unsigned RPMs cannot be un-signed; rollback is to regenerate repo from backup before signing (if backup exists)
3. **Repo sync**: Revert `.github/workflows/build.yml` to previous version; rsync permissions can be reverted by removing sudoers entry
4. **GPG key**: If key is compromised, revoke with `gpg --quick-revoke-key` and generate new key

## Dependencies

- GPG key exists on thinkcentre (confirmed: `397EEB9B...`)
- Passwordless sudo works for `glats` on rog (confirmed)
- `createrepo_c` available via `sudo nix shell` on rog (confirmed)
- `sops` configured for secret encryption in repo

## Success Criteria

- [ ] Runner auto-starts after `sudo reboot` on thinkcentre without manual intervention
- [ ] All 171 RPMs pass `rpm --checksig` with valid signature
- [ ] `mql repo sync` completes without manual sudo on rog
- [ ] GPG secret key exists in encrypted backup and can be imported
- [ ] CI workflow publishes signed RPMs and repodata successfully

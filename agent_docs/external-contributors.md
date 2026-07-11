# External Contributor Build Pipeline
<!-- stability: design-only | last-reviewed: 2026-07-10 -->

Phase 3 -- Design Only. Not Yet Implemented.

## Three-Phase Evolution

| Phase | What | Status |
|-------|------|--------|
| 1 | Order and document: --json output, maqui-build.yaml, docs, acceptance tests | Complete |
| 2 | CI remote: new build-rpms-v2.yml delegating to build-chain.sh, acceptance tests in CI | Complete |
| 3 | External contributors: per-PR overlay isolation, author gating, public logs | Design only |

Phase 3 is the natural extension of Phase 2. Once v2 CI is proven on push and
workflow_dispatch, external contributor support adds the isolation layer needed
for untrusted code from forks.

## How Phase 3 Works

### Trigger

1. PR is opened from a fork (or a branch in the main repo by a non-owner)
2. The `allowed_pr_authors` gate in `maqui-build.yaml` is checked
3. If `github.event.pull_request.user.login` is in `allowed_pr_authors`, CI runs
4. If the list is empty or the author is not in it, the build is skipped

### Per-PR Overlay Isolation

Instead of sharing the main overlay, each PR build gets its own isolated overlay:

```bash
# Create isolated overlay for PR #123
sudo mount -t overlay overlay \
  -o lowerdir=$MQL_ROOTFS/base,upperdir=$MQL_ROOTFS/layers/pr-123,workdir=$MQL_ROOTFS/layers/work-pr-123 \
  $MQL_ROOTFS/merged-pr-123

# Run build inside isolated chroot
sudo chroot $MQL_ROOTFS/merged-pr-123 /workspace/mql build <spec>

# Cleanup on PR close
sudo umount -l $MQL_ROOTFS/merged-pr-123
sudo rm -rf $MQL_ROOTFS/layers/pr-123 $MQL_ROOTFS/layers/work-pr-123
```

Design notes:
- `mql chroot --persist <pr-number>` would be the CLI interface (not yet implemented)
- Each PR overlay starts from a snapshot of the current base rootfs
- Changes in one PR overlay never affect another PR or the main overlay
- The main overlay (`$MQL_ROOTFS/merged`) is untouched by PR builds

### What Changes from Phase 2

| Aspect | Phase 2 (maintainer) | Phase 3 (external) |
|--------|---------------------|-------------------|
| Overlay | Shared `$MQL_ROOTFS/merged` | Per-PR isolated overlay |
| Repo sync | rsync to rog.local for push/merge | No sync from PR builds |
| GPG signing | Signs RPMs for release | No signing for PR builds |
| PR gate | None (maintainer pushes) | `allowed_pr_authors` check |
| Backup | Pre/post-build backups | No backup needed (throwaway overlay) |

### Lifecycle

1. PR opened by allowed author -> CI creates isolated overlay for PR number
2. CI runs build-chain.sh + acceptance-test.sh inside isolated overlay
3. RPMs + logs uploaded as GitHub Actions artifacts
4. PR merged -> standard publish workflow handles it (new commit to main triggers
   the v2 workflow which builds in the shared overlay, signs, and syncs)
5. PR closed unmerged -> cleanup runs via `if: always()` step, removing the PR
   overlay and its upper/work directories

### Security Considerations

- **Untrusted specs**: PR specs are not trusted. Build runs in an isolated
  overlay that cannot affect the main chroot state.
- **No GPG key exposure**: The signing key lives on the runner and is only used
  for push/merge builds. PR builds never sign RPMs.
- **No LAN access**: The runner has LAN access (to rog.local for sync). PR builds
  run in a context where sync steps are skipped. The workflow must ensure sync
  steps are guarded by a condition that PR builds cannot bypass.
- **Resource limits**: Multiple concurrent PR builds must not exhaust disk space.
  The cleanup step on PR close is mandatory.
- **Log visibility**: Build logs are uploaded as GitHub Actions artifacts tied to
  the PR. They are visible to anyone who can view the PR. No sensitive
  information (keys, tokens, passwords) should appear in logs.

### Push-vs-Read Boundary for External Contributors

| Direction | Mechanism | From | To | Who |
|-----------|-----------|------|----|-----|
| Push (internal) | SSH + rsync | runner | rog.local | Maintainer builds only |
| Push (internal) | bind-mount | Host workspace | Chroot | All builds |
| Read (public) | HTTPS (nginx) | rog.local | Internet | All users |
| Read (public) | GitHub artifacts | GitHub | PR viewer | PR participants |

The key difference from Phase 2: external PR builds never push to rog.local.
The only outward-facing result is GitHub Actions artifacts (logs + RPMs).

### Prerequisites for Implementation

- `mql chroot --persist <pr-number>` subcommand in `lib/chroot.sh`
- `allowed_pr_authors` field in `maqui-build.yaml` (schema exists in Phase 1)
- PR-scoped cleanup workflow (GitHub Actions `if: always()` step)
- Runner disk space monitoring for concurrent PR overlays

## Related Docs

- [Build Workflow](build-workflow.md) -- pipeline steps (shared overlay path)
- [Backup Flow](backup-flow.md) -- backup lifecycle for maintainer builds
- [Chroot Lifecycle](chroot-lifecycle.md) -- overlay state management
- `maqui-build.yaml` -- `allowed_pr_authors` configuration

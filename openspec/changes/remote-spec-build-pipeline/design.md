# Design: Remote Spec Build Pipeline

## Technical Approach

Three-phase build pipeline built on the existing overlay chroot and bash scripts. Phase 1 standardizes interfaces (JSON output, `maqui-build.yaml` schema, acceptance tests). Phase 2 refactors CI to call `build-chain.sh` instead of duplicating its own loop, adds per-spec status checks and structured verification. Phase 3 is design-only: per-PR overlay isolation with throwaway layers, gated by `allowed_pr_authors`.

## Architecture Decisions

### Decision: maqui-build.yaml Schema

**Choice**: Per-spec YAML in repo root with optional defaults fallback.

```yaml
# maqui-build.yaml
defaults:
  arches: [x86_64]
  verbose: false
  skip_tests: false

specs:
  - path: SPECS/bash.spec
    arches: [x86_64, i686]
    skip_tests: false
    verbose: false
  - path: SPECS/linux.spec
    arches: [x86_64]
    skip_tests: true

jobs:
  - trigger: push
    branch: main
    mode: publish
  - trigger: pull_request
    mode: validate

allowed_pr_authors: []  # Phase 3 gate; empty = no automatic PR builds
```

**Alternatives**: Per-spec `.maqui-build.yaml` alongside each spec file (rejected: scattered, hard to audit). Single `maqui-build.toml` (rejected: project uses YAML elsewhere).

**Rationale**: Single file maps to Packit's `packit.yaml` pattern. `defaults` block reduces repetition. Per-spec overrides are explicit. `allowed_pr_authors` at top level because it is a global security policy, not per-spec.

### Decision: Acceptance Test Step

**Choice**: New `scripts/acceptance-test.sh` runs post-build inside chroot, emits JSON.

```bash
./scripts/acceptance-test.sh <spec> [--arch=x86_64|i686] [--json]
```

Command sequence per spec:

1. `mql chroot --exec "rpm -q <package>"` -- verify installed
2. `mql chroot --exec "rpm -V <package>"` -- verify files intact
3. `mql chroot --exec "<binary> --version"` -- verify binary runs (if Provides binary)
4. `mql chroot --exec "ldd /usr/lib/<package>/*.so"` -- verify library linkage (if shared libs)
5. Collect results into structured JSON

Structured output format:

```json
{
  "spec": "bash",
  "arch": "x86_64",
  "timestamp": "2026-07-10T12:00:00Z",
  "status": "pass",
  "checks": [
    {"name": "rpm_installed", "status": "pass"},
    {"name": "rpm_verify", "status": "pass"},
    {"name": "binary_exec", "status": "pass", "detail": "bash --version exit 0"},
    {"name": "library_linkage", "status": "skip", "detail": "no shared libs"}
  ],
  "failures": []
}
```

**Alternatives**: Inline verification in build-chain.sh (rejected: harder to test in isolation). Python-based test runner (rejected: project is bash-only).

**Rationale**: Matches exploration section H.2 requirements. JSON output is machine-parseable by CI for per-spec status checks. Script is reusable by agents manually.

### Decision: CI Refactoring (Phase 2)

**Choice**: `build-rpms.yml` delegates to `build-chain.sh` replacing the inline build loop.

CI steps change:

| Current Step | New Step | Change |
|---|---|---|
| "Fetch sources and build" (40-line inline loop) | `./scripts/build-chain.sh "$SPECS" --json --state-file .ci-build-state` | Full delegation |
| Inline install + ldconfig | build-chain.sh calls `install_built_rpms()` | Already exists in build-chain.sh |
| No acceptance tests | `./scripts/acceptance-test.sh "$spec" --json >> acceptance-results.json` | New step after build |
| No artifacts | `actions/upload-artifact@v4` for `logs/`, `RPMS/`, `acceptance-results.json` | New step |
| No PR comment | `actions/github-script` posting summary from JSON state | New step |
| No retry | Retry fetch-step on exit code 28 (curl timeout) with `if: failure()` | New step |

Trigger detection stays: `scripts/detect-changed-specs.sh` (new Phase 1 script) replaces the inline `git diff` one-liner.

Error handling: build-chain.sh already stops on failure with state. CI reads `.ci-build-state` (JSON) to determine per-spec status. Failed specs get individual PR status checks.

**Alternatives**: Keep CI's own loop (rejected: duplicating build-chain.sh logic). Move everything to build-chain.sh invoked by GitHub Actions reusable workflow (overkill for now).

### Decision: Backup Flow

**Choice**: Automated pre-build backup, post-success backup, and post-failure restore.

```
pre-build  ->  build-chain.sh  ->  success?  ->  post-build backup
                                  |
                                  +->  failure?  ->  restore pre-build
```

CI flow:

1. **Pre-build**: `mql backup create pre-build-<tag>` (already in build-rpms.yml, keep it)
2. **Post-build success**: `mql backup create post-build-<tag>` (already exists, keep it)
3. **Post-build failure**: `if: failure()` step calls `mql backup restore pre-build-<tag>` (NEW)

How CI knows success/failure: GitHub Actions `if: failure()` / `if: success()` conditionals. The failure step is a separate workflow step that only runs when prior steps fail.

```yaml
- name: Restore on failure
  if: failure() && steps.list.outputs.specs != ''
  run: |
    TAG="${{ steps.list.outputs.tag }}"
    ./scripts/run-in-chroot.sh /workspace/mql backup restore "pre-build-$TAG"
```

**Rationale**: `lib/backup.sh` already has `backup_restore()`. CI just needs to call it on failure. Currently CI only prints "Restore: mql backup restore..." as a hint -- the new step actually does it.

### Decision: Push vs Read Boundary Documentation

**Choice**: New section in `agent_docs/backup-flow.md` and a pointer table in `AGENTS.md`.

| Direction | Mechanism | From | To | Who |
|---|---|---|---|---|
| Internal push | SSH + rsync | thinkcentre.local | rog.local | CI runner |
| Internal push | bind-mount | Host workspace | Chroot /mnt/workspace | CI runner |
| Public read | HTTPS (nginx) | rog.local | Internet | DNF5 clients, devs |

Agents verify boundary by checking: any SSH/rsync write targets `rog.local` (internal). Any HTTP/HTTPS URL is read-only public. Agents must never propose pushing directly to a public URL.

### Decision: Agent Knowledge Map Update

| File | Action | Content |
|---|---|---|
| `agent_docs/acceptance-tests.md` | Create | Verification step documentation, JSON schema, reusable by agents |
| `agent_docs/backup-flow.md` | Create | Backup lifecycle, restore-on-failure, push-vs-read boundary table |
| `agent_docs/build-workflow.md` | Modify | Add pointer to acceptance-tests.md and backup-flow.md; add JSON output section |
| `AGENTS.md` | Modify | Add 2 entries to pointer index; add acceptance test and backup paths to Key Paths |

New paths agents must know: none (existing overlay paths cover it).

New URLs: none (existing `repo.glats.org` and `maquiroot.glats.org` cover it).

### Decision: Phase 3 Isolation (outline only)

**Choice**: Per-PR overlay snapshot using `mql chroot --persist <pr-number>`.

Flow:

1. PR from allowed author -> CI detects `allowed_pr_authors` contains `github.event.pull_request.user.login`
2. CI creates isolated overlay: `sudo mount -t overlay overlay -o lowerdir=$MQL_ROOTFS/base,upperdir=$MQL_ROOTFS/layers/pr-<num>,workdir=$MQL_ROOTFS/layers/work-pr-<num> $MQL_ROOTFS/merged-pr-<num>`
3. Build runs inside isolated chroot; no sign, no sync, no promote
4. RPMs + logs uploaded as GitHub Actions artifacts
5. Cleanup: `sudo umount -l $MQL_ROOTFS/merged-pr-<num>; sudo rm -rf $MQL_ROOTFS/layers/pr-<num> $MQL_ROOTFS/layers/work-pr-<num>`

PR merged: existing publish workflow handles it -- a new commit to `main` triggers the standard build-rpms.yml publish flow. No promote from PR overlay needed.

PR closed unmerged: cleanup runs (GitHub Actions `if: always()` step).

**Alternatives**: Podman container (rejected for MVP: needs container image build pipeline). Copy-on-write filesystem overlay (rejected: overlayfs already provides this).

## Data Flow

```
SPEC change -> detect-changed-specs.sh -> build-chain.sh --json
  |                                      |
  +-> fetch-spec-sources.sh               +-> acceptance-test.sh --json
  +-> build-spec.sh (chroot)              +-> CI: upload artifacts
  +-> install-spec.sh (chroot)            +-> CI: PR comment (per-spec status)
  +-> backup (pre/post/restore)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `scripts/acceptance-test.sh` | Create | Post-build verification with JSON output |
| `scripts/detect-changed-specs.sh` | Create | Extract git diff spec detection from CI |
| `scripts/build-spec.sh` | Modify | Fix `--both` to build both arches; add `--json` flag |
| `scripts/build-chain.sh` | Modify | Add `--json` output for state file; add `--continue-on-failure` |
| `maqui-build.yaml` | Create | Declarative per-spec CI config schema |
| `.github/workflows/build-rpms.yml` | Modify | Delegate to build-chain.sh; add acceptance tests, artifacts, PR comments |
| `agent_docs/acceptance-tests.md` | Create | Acceptance test documentation |
| `agent_docs/backup-flow.md` | Create | Backup lifecycle + push-vs-read boundary |
| `agent_docs/build-workflow.md` | Modify | Add pointers to new docs; JSON output section |
| `AGENTS.md` | Modify | Add new agent_docs entries to pointer index |

## Interfaces / Contracts

### build-chain.sh --json state file format

```json
{
  "specs": [
    {"name": "bash", "status": "SUCCESS", "duration_s": 45, "log": "logs/bash-20260710.log"},
    {"name": "glibc", "status": "FAILED", "duration_s": 120, "log": "logs/glibc-20260710.log"}
  ],
  "summary": {"success": 1, "failed": 1, "skipped": 0, "total": 2}
}
```

### acceptance-test.sh JSON contract

See Architecture Decisions section above.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `--both` builds both arches | Build a small spec (e.g. zlib) with `--both`, verify RPMS/x86_64 and RPMS/i686 both have output |
| Unit | `acceptance-test.sh` JSON output | Run on installed package, validate JSON schema with `jq` |
| Integration | CI delegates to build-chain.sh | Trigger workflow_dispatch on a known spec, verify build-chain state file matches results |
| Integration | Backup restore on failure | Force a build failure, verify pre-build restore executes |
| E2E | PR validation mode | Open PR with spec change, verify status check and comment appear |

## Migration / Rollout

No data migration required. Phase 2 CI refactor can run in parallel with old workflow via a separate workflow file (`build-rpms-v2.yml`) during transition. Once verified, swap names. Rollback: revert to pre-refactor git tag.

## Open Questions

- [ ] Should `acceptance-test.sh` fail the CI build if a check fails, or report as warning? (Recommendation: fail on rpm_installed and rpm_verify; warn on binary_exec and library_linkage)
- [ ] Should `maqui-build.yaml` be validated at CI startup or per-build? (Recommendation: at CI startup with `yq` or `python3 -c 'import yaml'`)
- [ ] Retry count for transient fetch failures: 1 or 3? (Recommendation: 1 retry, 30s delay)
# Proposal: Remote Spec Build Pipeline

## Intent

Define a three-phase, spec-driven build pipeline for Maqui Linux. Phase 1 documents and orders the current artisanal build system. Phase 2 makes CI remote with automated verification. Phase 3 enables external contributors. The pipeline must be clean enough for AI agents to follow without mistakes.

## Scope

### In Scope

**Phase 1 (Order):** Fix `--both` flag in `build-spec.sh`. Add `--json` output to build-chain.sh. Create `agent_docs/acceptance-tests.md`, `agent_docs/backup-flow.md`, update `agent_docs/build-workflow.md` with full pipeline, update `docs/agents/standalone-developer.md` with setup paths. Document push-vs-read boundary in agent context. Create `maqui-build.yaml` schema (optional, Phase 2+).

**Phase 2 (CI Remote):** Refactor `.github/workflows/build-rpms.yml` to use `build-chain.sh`. Add per-spec GitHub status checks + PR comments. Upload build logs and RPM summaries as artifacts. Add structured build state (JSON). Add retry on transient failures. Add per-spec log verbosity from `maqui-build.yaml`. Add acceptance test verification step in CI.

**Phase 3 (External Contributors):** Design only. Build isolation per PR (overlay snapshot), `allowed_pr_authors` gate (empty initially), public log visibility via GitHub Actions. No LAN access required.

### Out of Scope

- Container-based build isolation (Phase 3 long-term, deferred)
- MCP server for build operations (future SDD change)
- Changing the overlay chroot model or spec file conventions
- Changing `mql` CLI interface or `mql.conf` format

## Capabilities

### New Capabilities

- `build-acceptance-tests`: Per-package verification after build -- `rpm -q`, `rpm -V`, binary `--version`, `ldd` linkage, file ownership checks
- `build-pipeline-config`: `maqui-build.yaml` schema for declarative per-spec CI settings (arches, skip_tests, verbose, allowed_pr_authors)
- `build-pipeline-documentation`: Agent knowledge docs covering backup flow, developer environment setup, push-vs-read surface boundary

### Modified Capabilities

- `ai-agent-stack`: `build-workflow.md` requirements (R.4) expand to cover full pipeline steps; new files (acceptance-tests.md, backup-flow.md) added to agent context index
- `agent-evolvability`: Stability classification (R.E3) extended for new agent_docs files; progressive disclosure architecture (R.E2) accommodates new Layer 1 files

## Approach

Three incremental phases, each gating the next. Phase 1 establishes clean, standardized interfaces (JSON output, documented boundaries) that Phase 2 consumes. Phase 2 replaces CI's duplicated build loop with `build-chain.sh` and adds structured verification. Phase 3 is design-only -- overlay isolation per PR with throwaway layers, building on the stable Phase 2 pipeline.

Key architectural constraint: push-vs-read boundary at `rog.local` nginx. Internal: SSH + rsync push. Public: HTTPS read via `repo.glats.org` and `maquiroot.glats.org`. All docs must make this boundary explicit.

## Affected Areas

| Area | Impact | Phase |
|------|--------|-------|
| `scripts/build-spec.sh` | Fix `--both` flag | 1 |
| `scripts/build-chain.sh` | Add `--json` output | 1 |
| `agent_docs/build-workflow.md` | Expand to full pipeline | 1 |
| `agent_docs/acceptance-tests.md` | New | 1 |
| `agent_docs/backup-flow.md` | New | 1 |
| `agent_docs/mql-cli-reference.md` | Update | 1 |
| `docs/agents/standalone-developer.md` | Add setup paths | 1 |
| `maqui-build.yaml` | New schema | 1 |
| `.github/workflows/build-rpms.yml` | Refactor to build-chain.sh | 2 |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `--both` fix breaks existing x86_64 builds | Low | i686 loop is additive; x86_64 path unchanged |
| `build-chain.sh` refactor changes behavior | Med | Run in parallel with old CI loop during transition |
| Overlay isolation for Phase 3 is fragile | High | Design only in this change; implement when Phase 2 is stable |
| `rog.local` nginx boundary not respected in docs | Low | Explicit boundary table in all docs; agents verify during build |

## Rollback Plan

- **Phase 1**: Revert individual commits. `--both` fix is isolated to one function in build-spec.sh.
- **Phase 2**: Old CI workflow recoverable from git history. Re-deploy from pre-refactor tag if needed.
- **Phase 3**: Design document only -- no runtime rollback needed.

## Dependencies

None external. All build infrastructure (rootfs, chroot, runner, GPG key, SSH to rog.local) exists on `thinkcentre.local`.

## Success Criteria

- [ ] `--both` flag builds both x86_64 and i686 correctly
- [ ] CI uses `build-chain.sh` (no duplicated build loop)
- [ ] Every build runs acceptance tests (rpm -q, rpm -V, binary test)
- [ ] Pre-build and post-build backups created automatically
- [ ] Build logs uploaded as GitHub Actions artifacts
- [ ] PR receives per-spec status comment (success/failure per package)
- [ ] Developer setup documented for Nix shell and standalone paths
- [ ] Push-vs-read boundary documented in agent context
- [ ] Agent knowledge map updated with new paths and URLs
- [ ] Phase 3 design documented (implementation deferred)

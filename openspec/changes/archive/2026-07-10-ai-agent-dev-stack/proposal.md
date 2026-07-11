# Proposal: AI Agent Stack for Maqui Linux Spec-Driven Development

## Intent

AI agents (OpenCode, Claude Code, Cursor, Copilot) currently lack structured context to build RPM packages for Maqui Linux. The root `AGENTS.md` (210 lines) is a flat dump exceeding the 200-line cross-tool budget. No domain reference files exist. The stack must be evolvable -- mql CLI, paths, and CI/CD will change as the distro matures.

## Scope

### In Scope
- Rewrite `AGENTS.md` to 150-200 lines: entry point + pointer index + gotchas + context-version marker
- Create `CLAUDE.md` symlink to `AGENTS.md` for Claude Code compatibility
- Create `agent_docs/` with 7 domain reference files: distro-identity, build-workflow, spec-conventions, chroot-lifecycle, dependency-resolution, mql-cli-reference, troubleshooting
- Regenerate `mql-cli-reference.md` from `mql --help` output (single source of truth)
- Include `agent-context-version: "1"` marker in AGENTS.md

### Out of Scope
- `.opencode/skills/maqui-build/` and `maqui-spec-create/` (Phase 2)
- MCP server `maqui-build` (Phase 3)
- `.cursor/rules/`, `.github/copilot-instructions.md` (deferred until tool adoption evidence)
- Pre-commit hooks or CI validation for context freshness (Phase 2)
- NixOS declarative config changes

## Capabilities

### New Capabilities
- `agent-context-stack`: Cross-tool entry point (AGENTS.md) with domain reference files (agent_docs/) providing on-demand context for spec-driven RPM development
- `agent-evolvability`: Context version marker, regenerable CLI reference from source-of-truth, progressive disclosure architecture

### Modified Capabilities
None -- no existing SDD specs to modify.

## Approach

**Architecture**: Three-layer progressive disclosure -- AGENTS.md (150-200 lines, always loaded) points to `agent_docs/` (7 files, loaded on demand). Symlink `CLAUDE.md -> AGENTS.md` bridges Claude Code.

**Agent flow on startup**: Agent reads `AGENTS.md` (identity, constraints, gotchas, doc index). When building a spec, agent loads `agent_docs/build-workflow.md` and `agent_docs/spec-conventions.md`. When debugging, loads `agent_docs/troubleshooting.md`.

**Evolvability**: `agent-context-version: "1"` in AGENTS.md detects format changes. `mql-cli-reference.md` regenerates from `mql --help`. Files annotated with stability: Stable (distro-identity, spec-conventions), Mostly Stable (build-workflow, chroot-lifecycle), Evolvable (mql-cli-reference, troubleshooting).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `AGENTS.md` | Rewritten | 210 -> 150-200 lines, pointer index replaces inline docs |
| `CLAUDE.md` | Created | Symlink to AGENTS.md |
| `agent_docs/` | Created | 7 reference files (new directory) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| AGENTS.md over 200 lines after Phase 2 additions | Medium | Hard budget rule; new context goes to agent_docs/, not root |
| `mql --help` output changes break regenerability contract | Low | CLI reference is regenerable, not manual; regenerate on CLI change |
| agent_docs/ drift from reality (stale paths, outdated commands) | Medium | Phase 2 pre-commit hook; regenerate CI check |
| Claude Code symlink breaks on Windows | Low | Maqui dev is Linux-only; symlink is POSIX standard |

## Rollback Plan

1. `git revert` the commit that introduces this change
2. Remove `CLAUDE.md` symlink and `agent_docs/` directory
3. Restore `AGENTS.md` from prior commit (current 210-line version)

No data loss risk -- all new files are additive or rewrites of tracked artifacts.

## Dependencies

- `mql --help` must be runnable to generate `agent_docs/mql-cli-reference.md` (Nix dev shell or standalone)
- `docs/DISTRO-IDENTITY.md` exists as source for `agent_docs/distro-identity.md`

## Success Criteria

- [ ] `AGENTS.md` is 150-200 lines and opens with version marker
- [ ] `CLAUDE.md` is a valid symlink to `AGENTS.md`
- [ ] All 7 `agent_docs/` files exist with correct content and stability annotations
- [ ] `agent_docs/mql-cli-reference.md` matches current `mql --help` output
- [ ] All file paths referenced in `agent_docs/` resolve to existing repo files
- [ ] Fresh agent session follows `AGENTS.md` pointer index to load correct domain docs

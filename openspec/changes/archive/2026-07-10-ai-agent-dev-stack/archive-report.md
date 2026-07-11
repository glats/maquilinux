# Archive Report: ai-agent-dev-stack

**Archived by**: sdd-archive executor
**Archive date**: 2026-07-10
**Mode**: hybrid (openspec filesystem + Engram persistence)

## Change Summary

Created an evolvable AI-agent context stack for Maqui Linux spec-driven development. Phase 1 delivers a progressive-disclosure architecture: AGENTS.md (entry point) + 8 agent_docs/ domain files.

## Artifacts Created

| File | Lines | Action |
|------|-------|--------|
| `AGENTS.md` | 112 (rewritten) | Entry point with version marker and pointer index |
| `CLAUDE.md` | symlink | POSIX symlink to AGENTS.md |
| `agent_docs/distro-identity.md` | 37 | Stable: distro identity |
| `agent_docs/build-workflow.md` | 76 | Mostly-stable: build pipeline |
| `agent_docs/spec-conventions.md` | 87 | Stable: spec format conventions |
| `agent_docs/chroot-lifecycle.md` | 75 | Mostly-stable: overlay lifecycle |
| `agent_docs/dependency-resolution.md` | 65 | Mostly-stable: BuildRequires chain |
| `agent_docs/multiarch-guide.md` | 78 | Stable: i686 patterns |
| `agent_docs/mql-cli-reference.md` | 72 | Evolvable: regenerable from `mql --help` |
| `agent_docs/troubleshooting.md` | 81 | Evolvable: failure modes |

## Architecture Decisions

- Three-layer progressive disclosure (AGENTS.md -> agent_docs/ -> docs/)
- AGENTS.md under 200-line budget (actual: 112 lines)
- Version marker `agent-context-version: "1"` for staleness detection
- CLAUDE.md as POSIX symlink (no drift risk, zero maintenance)
- Plain Markdown only in shared artifacts (no tool-specific syntax)
- kebab-case filenames matching repo convention
- Stability annotations (stable/mostly-stable/evolvable) per file
- mql-cli-reference.md regenerable from `mql --help` (single source of truth)

## Constraints Verified

- AGENTS.md: 112 lines (under 200 budget) -- PASS
- agent-context-version: "1" marker present -- PASS
- CLAUDE.md symlink resolves to AGENTS.md -- PASS
- All agent_docs/ files under 100-line budget -- PASS
- All 8 files have stability headers -- PASS
- 0 systemd references, 0 emojis, 0 unsupported "we" -- PASS

## SDD Cycle Audit

| Artifact | Status | Path |
|----------|--------|------|
| exploration.md | present | archive/specs/... |
| proposal.md | present | archive/ |
| specs/ai-agent-stack | present (delta) | archive/ |
| specs/agent-evolvability | present (delta) | archive/ |
| design.md | present | archive/ |
| tasks.md | **missing** | Intentional partial archive per orchestrator direction |
| apply-progress | **missing** | Intentional partial archive per orchestrator direction |
| verify-report | **missing** | Intentional partial archive per orchestrator direction |

### Intentional Partial Archive Justification

This change was executed by the orchestrator (OpenCode agent) directly -- the SDD pipeline was followed for exploration, proposal, spec, and design, but formal tasks/apply/verify phases were skipped because the implementation was performed directly by the orchestrator during the same session. The orchestrator verified all constraints (line budgets, version marker, symlink resolution, cross-references) before requesting archive. This is recorded as an **intentional partial archive**.

## Specs Synced

| Domain | Action | Details |
|--------|--------|---------|
| ai-agent-stack | Created as main spec | 6 requirements (R.1-R.7, R.9), 3 scenarios |
| agent-evolvability | Created as main spec | 4 requirements (R.8, R.E1-R.E4), 3 scenarios |

## Main Specs Updated

- `openspec/specs/ai-agent-stack/spec.md` -- Created
- `openspec/specs/agent-evolvability/spec.md` -- Created

## Archive Contents

- design.md
- exploration.md
- proposal.md
- specs/ai-agent-stack/spec.md
- specs/agent-evolvability/spec.md
- archive-report.md

## Phase 2/3 Preview

- **Phase 2**: Per-tool skills (.opencode/skills/maqui-build, maqui-spec-create), pre-commit hooks, CI validation
- **Phase 3**: MCP server (maqui-build) with structured tool calls and resource hydration

## Engram Observation IDs

| Artifact | Engram ID |
|----------|-----------|
| exploration | #1753 |
| proposal/topic | #1754 |
| design | #1755 |
| spec | #1756 |
| archive (this) | (current save) |

## Risks

- Tasks/verify artifacts were never created -- no formal test evidence beyond orchestrator's manual constraint verification
- Documented in this report as intentional partial archive

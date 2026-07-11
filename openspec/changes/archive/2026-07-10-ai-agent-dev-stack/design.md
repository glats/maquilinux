# Design: AI Agent Stack for Maqui Linux

## Technical Approach

Three-layer progressive disclosure: AGENTS.md (root, <200 lines, always loaded) points to `agent_docs/` (7 domain files, <100 lines each, loaded on demand). CLAUDE.md is a symlink to AGENTS.md. A version marker enables staleness detection. All files are plain Markdown — no tool-specific syntax in shared artifacts.

## Architecture Decisions

### Decision: AGENTS.md section structure

**Choice**: Reorder for agent startup efficiency — identity and constraints first, commands second, gotchas third, pointer index fourth, policy last.

**Alternatives**: Keep current order (project → config → paths → rootfs → specs → CLI → packages → CI/CD → docs → gotchas → language).

**Rationale**: ETH Zurich 2026 study shows agents benefit from commands, constraints, and gotchas — not architecture overviews. High-signal content at the top reduces token waste on startup.

### Decision: What stays vs moves to agent_docs/

| Content | Stays in AGENTS.md | Moves to agent_docs/ |
|---------|-------------------|---------------------|
| Project identity (1 paragraph) | Yes | — |
| Config system (2-file, MQL_ROOTFS) | Yes (condensed) | — |
| Key paths (8 most critical) | Yes (top 8) | Full list → chroot-lifecycle.md |
| Critical gotchas (top 4) | Yes | All gotchas → troubleshooting.md |
| Language policy | Yes | — |
| Decision policy ref | Yes | — |
| Full CLI reference | — | mql-cli-reference.md |
| Spec conventions detail | — | spec-conventions.md |
| Self-hosting package table | — | build-workflow.md |
| CI/CD operations detail | — | Troubleshooting.md (pointer to docs/agents/) |
| Full documentation index | — | Restructured as pointer index |
| Rootfs/overlay mechanics | — | chroot-lifecycle.md |
| Multiarch patterns | — | multiarch-guide.md |

### Decision: AGENTS.md proposed outline (190 lines target)

```
# AGENTS.md -- Maqui Linux
<!-- agent-context-version: "1" -->

## Project                          (8 lines: identity paragraph)
## Critical Constraints             (6 lines: English-only, no emojis, spec=source of truth)
## Quick Commands                    (12 lines: 7 most common mql commands)
## Critical Gotchas                  (20 lines: top 4 with one-liner each)
## Agent Documentation Index        (30 lines: pointer table to agent_docs/ + docs/)
## Configuration                     (12 lines: 2-file config, MQL_ROOTFS)
## Key Paths                         (16 lines: top 8 paths table)
## Language and Policy               (8 lines: English-only, decision framework ref)
## Context Stack Structure          (12 lines: how this file + agent_docs/ works)
## Rules for This File               (5 lines: 200-line budget, update protocol)
                                    (~129 lines + headers ≈ 190)
```

### Decision: agent_docs/ file naming and structure

**Choice**: kebab-case filenames, matching existing repo convention (`docs/agents/runner-setup.md`). Each file has a standard header block:

```markdown
# {Title}
<!-- stability: stable|mostly-stable|evolvable | last-reviewed: YYYY-MM-DD -->

## {Sections...}
```

**Alternatives**: snake_case (rejected — inconsistent with repo), PascalCase (rejected).

**Rationale**: Consistency with existing `docs/` naming. Stability annotation tells agents (and humans) how much to trust the file.

### Decision: The 7 agent_docs/ files

| File | Role | Stability | Line Budget |
|------|------|-----------|-------------|
| `distro-identity.md` | What Maqui is, characteristics, versioning | stable | ~60 |
| `build-workflow.md` | Spec→fetch→build→install→repo steps + self-hosting packages | mostly-stable | ~80 |
| `spec-conventions.md` | Gen3 format, release tag, %files, macros | stable | ~80 |
| `chroot-lifecycle.md` | Overlay layers, bind mounts, virtual FS, rootfs paths, state mgmt | mostly-stable | ~80 |
| `mql-cli-reference.md` | Full command listing with flags (REGENERABLE from `mql --help`) | evolvable | ~80 |
| `troubleshooting.md` | Known failure modes, stale mount recovery, build debugging | evolvable | ~80 |
| `multiarch-guide.md` | i686 patterns, library dirs, ExclusiveArch, 32-bit copy pattern | stable | ~80 |

### Decision: Cross-referencing between agent_docs/

**Choice**: Relative-path Markdown links at the end of each file under a "Related Docs" section:

```markdown
## Related Docs
- [Build Workflow](build-workflow.md) — full build procedure
- [Spec Conventions](spec-conventions.md) — Gen3 spec format
```

**Rationale**: Agents can follow Markdown links. No tool-specific import syntax. Works across all tools.

### Decision: CLAUDE.md approach

**Choice**: POSIX symlink `ln -s AGENTS.md CLAUDE.md`. No Claude-specific extensions in Phase 1.

**Alternatives**: Separate file with redirect (rejected — causes drift). Separate CLAUDE.md with @import (rejected — @import is Claude Code only, Phase 2 if needed).

**Rationale**: Symlink is zero-maintenance. No drift risk. Maqui dev is Linux-only so POSIX symlinks work.

### Decision: Evolvability version system

**Choice**: HTML comment marker `<!-- agent-context-version: "1" -->` at the top of AGENTS.md. Manual increment. Agent warns on mismatch.

| Aspect | Decision |
|--------|----------|
| Where declared | AGENTS.md line 2 (HTML comment) |
| What "stale" means | Version mismatch: agent's last-known version != file version |
| Detection | Agent reads version on startup, compares to its internal expectation |
| Agent action | WARN user (never refuse, never auto-update) |
| Increment | Manual, in same PR that changes the format/structure |
| Regenerable files | `mql-cli-reference.md` generated from `mql --help`; stability tag = evolvable |

**Rationale**: HTML comments are invisible in rendered Markdown (no visual noise) but parseable by agents. Warning-only prevents blocking work on false staleness. Manual increment ensures intentional version bumps.

### Decision: Cross-tool compatibility strategy

| Feature | OpenCode | Claude Code | Copilot/VSCode | Common Denominator |
|---------|----------|-------------|-----------------|-------------------|
| AGENTS.md | Yes (native) | Yes (via CLAUDE.md symlink) | Yes (native) | **Yes — primary artifact** |
| agent_docs/ (plain .md) | Manual load | Manual load | Manual load | **Yes — via pointer index** |
| Skills (SKILL.md) | .opencode/skills/ | .claude/skills/ | N/A | Phase 2 (per-tool) |
| @import | Not supported | Supported | Not supported | **Not used in shared files** |
| Path-scoped globs | Not supported | Supported (frontmatter) | Supported | **Not used in shared files** |
| MCP servers | Yes | Yes | Partial | Phase 3 |

**Rule**: Shared artifacts (AGENTS.md, agent_docs/) use ONLY plain Markdown — no frontmatter globs, no @import, no tool-specific syntax. Tool-specific features are isolated to tool-specific directories (`.opencode/`, `.claude/`).

### Decision: Integration with existing repo files

| Relationship | Approach |
|-------------|----------|
| AGENTS.md ↔ README.md | AGENTS.md is for agents; README.md is for humans. No duplication. AGENTS.md doesn't duplicate README content. |
| AGENTS.md ↔ docs/DISTRO-IDENTITY.md | AGENTS.md has 1-line identity summary + pointer. agent_docs/distro-identity.md is an AI-optimized extract. |
| agent_docs/distro-identity.md ↔ docs/DISTRO-IDENTITY.md | agent_docs version is condensed, action-oriented (what an agent needs to know). docs/ version is canonical human reference. Both point to each other. |
| AGENTS.md ↔ docs/agents/*.md | AGENTS.md pointer index references existing docs/agents/ files for CI/CD ops. No duplication. |
| AGENTS.md ↔ mql.conf | AGENTS.md describes config system briefly. mql.conf is the source of truth for config values. |

### Decision: Anti-pattern mitigations

| Anti-pattern | Mitigation |
|-------------|------------|
| Context inflation | Root AGENTS.md <200 lines. agent_docs/ loaded on demand only. |
| Stale references | Each agent_docs/ file has `last-reviewed` date. Phase 2: pre-commit hook validates paths exist. |
| Tool-specific syntax | Shared files use plain Markdown only. Tool features isolated to .opencode/, .claude/. |
| Over-promising | AGENTS.md describes commands, not autonomous capability. Agents get reference, not build bots. |
| Referencing nonexistent docs | Pointer index only lists files that exist. Tasks phase validates all paths. |

## Data Flow

```
Agent startup
     │
     ▼
AGENTS.md (<200 lines: identity, constraints, commands, gotchas, pointer index)
     │
     │  Agent encounters task domain (build, debug, spec creation)
     │
     ▼
agent_docs/{relevant-file}.md (loaded on demand, <100 lines each)
     │
     │  Agent needs deeper context (human docs, CI/CD ops)
     │
     ▼
docs/ (human-facing documentation, referenced by pointer index)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `AGENTS.md` | Rewrite | 210→~190 lines, reordered, pointer index, version marker |
| `CLAUDE.md` | Create | Symlink to AGENTS.md |
| `agent_docs/distro-identity.md` | Create | AI-optimized distro identity extract (~60 lines) |
| `agent_docs/build-workflow.md` | Create | Build procedure + self-hosting packages (~80 lines) |
| `agent_docs/spec-conventions.md` | Create | Gen3 spec format rules (~80 lines) |
| `agent_docs/chroot-lifecycle.md` | Create | Overlay model, bind mounts, state management (~80 lines) |
| `agent_docs/mql-cli-reference.md` | Create | Full CLI reference, regenerated from `mql --help` (~80 lines) |
| `agent_docs/troubleshooting.md` | Create | Known failure modes and recovery (~80 lines) |
| `agent_docs/multiarch-guide.md` | Create | i686 conditional patterns and library layout (~80 lines) |

## Interfaces / Contracts

### agent_docs/ file header contract

Every agent_docs/ file MUST start with:

```markdown
# {Human-Readable Title}
<!-- stability: {stable|mostly-stable|evolvable} | last-reviewed: YYYY-MM-DD -->

{Content sections...}

## Related Docs
- [Related File Name](filename.md) — one-line description
- [External Doc](../docs/path.md) — one-line description
```

### AGENTS.md pointer index contract

The pointer index table format:

```markdown
## Agent Documentation Index

| File | What it covers | Stability |
|------|---------------|-----------|
| `agent_docs/build-workflow.md` | Spec→build→install→repo procedure | mostly-stable |
| `agent_docs/spec-conventions.md` | Gen3 spec format, release tags | stable |
| ... | ... | ... |
```

### Version marker contract

```html
<!-- agent-context-version: "1" -->
```

- Lives on line 2 of AGENTS.md (immediately after H1 title)
- Incremented manually when AGENTS.md structure changes
- Agent reads and compares to its expected version
- Mismatch → agent prints warning, continues working

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Structural | AGENTS.md under 200 lines | `wc -l` check |
| Structural | Each agent_docs/ file under 100 lines | `wc -l` per file |
| Link integrity | All paths referenced in agent_docs/ exist | Script that resolves every relative path |
| Symlink | CLAUDE.md resolves to AGENTS.md | `readlink CLAUDE.md` |
| Content | mql-cli-reference.md matches `mql --help` | Diff generated output against file |
| Functional | Fresh agent session follows pointer index to correct domain doc | Manual: prompt agent with "build package X", verify it loads build-workflow.md |

## Migration / Rollout

No migration required. All changes are additive (new files) or a rewrite of existing tracked file (AGENTS.md). Rollback: `git revert` the introducing commit.

## Open Questions

- [ ] Should `agent_docs/mql-cli-reference.md` be git-tracked or .gitignored + generated in CI? Git-tracked is simpler for Phase 1; CI generation is cleaner for Phase 2.
- [ ] Should the pointer index in AGENTS.md use Markdown links or plain `agent_docs/filename.md` text? Links are clickable in editors; plain text is simpler. Recommendation: plain text (agents parse it either way).
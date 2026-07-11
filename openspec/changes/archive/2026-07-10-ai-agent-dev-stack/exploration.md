# Exploration: AI Agent Stack for Maqui Linux Spec-Driven Development

## Current State

Maqui Linux is an independent, self-hosting Linux distribution (x86_64 + i686 multiarch) built from source with RPM/DNF5 + OpenRC. The `mql` CLI orchestrates all development through an overlayfs-based chroot workflow. AI agents (primarily OpenCode) are configured via `~/.config/opencode/` which is managed declaratively through NixOS Home Manager (`~/.nixos/shared/opencode.nix`). The project currently has an `AGENTS.md` (210 lines) at the repo root providing an overview, CLI reference, and critical gotchas. However, there is no structured agent context stack that gives AI tools the full knowledge required to build RPM packages end-to-end. This exploration maps what is needed, what mechanisms exist, and proposes a minimal viable architecture.

---

## A. Maqui Build Process Map

### Step-by-Step Workflow: "I want to add package X" to "RPM is in the repo"

```
1. CREATE SPEC → 2. FETCH SOURCE → 3. MOUNT OVERLAY → 4. BUILD → 5. INSTALL → 6. REPO UPDATE
```

#### Step 1: Create/Edit Spec File
- **Location**: `SPECS/<name>.spec`
- **Format**: Gen3 RPM spec with Maqui-specific conventions:
  - Debug packages disabled globally (`%global debug_package %{nil}`)
  - Release tag: `1.m264%{?dist}` (m264 = Maqui Linux 26.4)
  - Library dirs: `/usr/lib/x86_64-linux-gnu/` (64-bit), `/usr/lib/i386-linux-gnu/` (32-bit)
  - Multiarch conditionals: `%if "%{_target_cpu}" == "i686"` blocks
  - `BuildRequires:` must resolve against available packages in the repo
- **Reference**: `SPECS/SPEC_TEMPLATE.md` (Gen3 conventions), `SPECS/openssl.spec` (example)

#### Step 2: Fetch Sources
- **Script**: `scripts/fetch-spec-sources.sh`
- Sources (tarballs, patches) go in `SOURCES/`
- `build-spec.sh` validates source existence before build via `check_sources()`
- Sources are accessed in chroot via workspace bind mount at `/workspace/SOURCES`

#### Step 3: Mount Overlay Chroot
- **Command**: `mql chroot --mount` (or `sudo mql chroot` to enter interactively)
- **Mechanism**: overlayfs merges immutable `$MQL_ROOTFS/base/` + writable `$MQL_ROOTFS/layers/upper/`
- **Bind mounts**: workspace (project root) at `/mnt/workspace`, RPMS at `/mnt/repo`
- **Virtual FS**: proc, sys, dev, dev/pts, dev/shm, run, tmpfs
- **Repo config**: `/etc/yum.repos.d/maquilinux-local.repo` points to `file:///mnt/repo`
- **Rootfs path**: `$MQL_ROOTFS` (env var) > `$MQL_DISK` > `/mnt/maquilinux` (default)

#### Step 4: Build RPM (in chroot)
- **Command**: `mql build <spec>` (wraps `scripts/build-spec.sh`)
- **Flow**:
  1. `verify_chroot()` -- checks overlay mounted, workspace bind-mounted, rpmbuild exists
  2. `check_sources()` -- extracts Source0 from spec, expands macros, verifies file exists
  3. `run_rpmbuild_in_chroot()` -- constructs rpmbuild command with `_topdir /workspace`, all dirs under `/workspace`
  4. Executes via `chroot` with clean environment (`env -i HOME=/root TERM=xterm PATH=...`)
- **Flags**: `--both` (x86_64 + i686), `--arch=`, `--skip-tests/--nocheck`, `--nodeps`
- **Output**: RPMs in `RPMS/<arch>/` directory

#### Step 5: Install RPM (in chroot)
- **Command**: `mql install <spec>` (wraps `scripts/install-spec.sh`)
- Uses DNF5 from local repo: `dnf install /mnt/repo/<pkg>-*.rpm --nogpgcheck`
- Installs into overlay upper layer (can be promoted to base)

#### Step 6: Update Repo Metadata
- **Command**: `mql repo update`
- Runs `createrepo_c` for each arch subdirectory in `RPMS/`
- Repo sync: `mql repo sync` → rsync to `repo.glats.org`

### Overlay State Management
| Command | Purpose |
|---------|---------|
| `mql chroot --reset` | Discard overlay changes (clear upper/work) |
| `mql chroot --persist <name>` | Snapshot upper layer as tar.xz in `backup/` |
| `mql chroot --promote` | Merge overlay into base (interactive confirm, irreversible) |
| `mql backup create [tag]` | Museum-style rootfs backup |

### Common Failure Modes
1. **Overlay not mounted** -- must run `mql chroot --mount` first
2. **Source not found** -- run `scripts/fetch-spec-sources.sh <spec>` first
3. **BuildRequires unresolved** -- package dependencies must be built and installed in order
4. **i686 detection** -- `supports_i686()` checks spec for i686 markers; `ExclusiveArch: x86_64` blocks 32-bit
5. **Stale overlay mounts after crash** -- use `sudo umount -l` in reverse order
6. **`mql chroot --promote` requires interactive confirmation** -- cannot be scripted silently
7. **DNF5 GPG errors** -- `--nogpgcheck` required until PGP signing is implemented (Phase 3)

### Multiarch Path (`--both`)
- Specs use `%if "%{_target_cpu}" == "i686"` conditionals
- Single spec builds both architectures via copy-to-32 pattern (e.g., openssl.spec)
- Library paths differ: `/usr/lib/x86_64-linux-gnu/` vs `/usr/lib/i386-linux-gnu/`
- `supports_i686()` function checks for `-m32`, `i686-pc-linux-gnu`, `_target_cpu` references
- `ExclusiveArch: x86_64` disables i686 for a spec
- Current limitation: `--both` builds x86_64 only; i686 must be run separately

### What an Agent Needs to Know at Each Step

| Step | Knowledge Required |
|------|-------------------|
| Create Spec | Gen3 conventions, multiarch patterns, release tag format, library dirs, BuildRequires resolution |
| Fetch Sources | Source URL pattern, SOURCES/ directory, script location |
| Mount Overlay | Rootfs path resolution, bind mount order, virtual FS requirements |
| Build RPM | Chroot execution pattern, environment variables, rpmbuild flags, arch target strings |
| Install RPM | DNF5 command format, local repo path, --nogpgcheck requirement |
| Repo Update | createrepo_c command, arch subdirectories, sync host/path |
| Debug | Stale mount recovery, build failure diagnostics, dependency chain analysis |

---

## B. OpenCode Integration Points

### File Structure of `~/.config/opencode/`

```
~/.config/opencode/
├── opencode.json          # Primary config (generated by NixOS HM)
├── AGENTS.md              # Global skill index (triggers + paths)
├── IDENTITY.md            # Persona and response protocol
├── PERSONA.md             # Detailed persona definition
├── SYSTEM_RULES.md        # Global rules (language policy, research, delegation)
├── sdd-orchestrator.md    # SDD orchestrator agent prompt
├── sdd-review-policy.md   # SDD review policy
├── CAVEMAN_RULES.md       # Caveman mode rules
├── tui.json               # TUI plugin config
├── package.json           # npm packages for TUI plugins
├── instructions/
│   └── universal.md       # Universal agent instructions
├── commands/              # Custom commands
├── plugins/               # Plugin .ts files
└── skills/                # 33 skill directories, each with SKILL.md
    ├── _shared/           # Shared SDD reference docs
    ├── sdd-*/             # SDD workflow skills
    ├── cavecrew*/         # Caveman subagent skills
    ├── branch-pr/         # Gentle AI workflow skills
    ├── skill-creator/     # Meta-skill
    └── ...                # Other utility skills
```

### How Skills Work

1. **Location**: Skills are searched in 6 locations:
   - Project: `.opencode/skills/<name>/SKILL.md`
   - Global: `~/.config/opencode/skills/<name>/SKILL.md`
   - Claude-compatible: `.claude/skills/<name>/SKILL.md`, `~/.claude/skills/<name>/SKILL.md`
   - Agent-compatible: `.agents/skills/<name>/SKILL.md`, `~/.agents/skills/<name>/SKILL.md`

2. **Format**: Each skill is a `SKILL.md` file with YAML frontmatter:
   ```yaml
   ---
   name: skill-name
   description: "What this skill does. Trigger: when to load."
   disable-model-invocation: true   # For delegate-only skills
   user-invocable: false            # Not invokable by user directly
   license: MIT
   metadata:
     author: author-name
     version: "1.0"
     delegate_only: true            # Orchestrator gate
   ---
   ```

3. **Loading**: Skills are listed in `AGENTS.md` with trigger conditions. The model detects context and loads the skill via `skill()` tool. Some skills include an orchestrator gate (delegate_only) that prevents inline execution.

4. **Extension Points**:
   - Skills can bundle reference files, scripts, and assets alongside SKILL.md
   - Skills are synced from OpenCode to OpenFang (another agent framework)
   - Project-level skills take precedence over global skills

### NixOS Declarative Configuration

OpenCode is managed declaratively via `~/.nixos/shared/opencode.nix`:
- **Providers**: Defined in `providers.nix`, agent models per SDD phase
- **MCP Servers**: Base set in `mcps-base.nix`, extensible via `extraMcps`
- **Agents**: SDD phase agents with model assignments
- **Permissions**: Tool-level allow/deny/ask rules
- **Skills**: Deployed from `gentle-ai-assets` package as part of NixOS activation
- **Configuration pipeline**: Nix generates `opencode.json` → HM creates symlinks → activation script converts to mutable copies → plugin runtime setup

### MCP Server Integration

Currently configured MCP servers (in `mcps-base.nix`):
- `context7` -- documentation lookup
- `engram` -- persistent memory
- `github-personal` / `github-work` -- GitHub API (dual auth)
- `exa` -- web search
- `nixos` -- NixOS/Nix package and option search

MCP servers are declared in `opencode.json` under the `mcp` key. Each server has a `command` (for stdio) or `url` (for HTTP), environment variables, and a `type` field.

### Project-Level vs User-Level Config

- **User-level** (`~/.config/opencode/`): Global skills, persona, system rules, MCP servers, identity
- **Project-level** (`.opencode/`): Project-specific skills, project-level `opencode.json` overrides
- **Precedence**: Project files override user files for the same key
- **Skills**: Project `.opencode/skills/` searched first, then `~/.config/opencode/skills/`

### Key Discovery: Skills are NOT Nix-managed per-project

All current skills live in `~/.config/opencode/skills/` (global, Nix-managed). There is NO per-project `.opencode/` or `.claude/` directory in the Maqui Linux repo. Project-specific skills for Maqui build context would need to be added in one of:
- `~/Project/maquilinux/.opencode/skills/` (project config, portable)
- `~/Project/maquilinux/.claude/skills/` (Claude-compatible, portable)
- `~/.config/opencode/skills/` (global, Nix-managed, not Git-tracked with the repo)

---

## C. Cross-Platform Agent Context Patterns

### AGENTS.md -- The Emerging Cross-Tool Standard

**Status**: Stewarded by the Agentic AI Foundation under Linux Foundation. Supported by 60+ tools including OpenAI Codex, GitHub Copilot, Cursor, Windsurf, Aider, Zed, Devin, JetBrains Junie, and VS Code.

**Key characteristics**:
- Plain Markdown, no required schema or special syntax
- Hierarchy: closest file to edited code wins; explicit user prompts override everything
- Subdirectory support: nested `AGENTS.md` files for monorepos (OpenAI has 88 in their main repo)
- Used by 60,000+ open-source repositories

**What works**: Project overview, build/test commands, code conventions, gotchas, non-obvious constraints

**What doesn't work** (per ETH Zurich 2026 study):
- LLM-generated context files have a marginal NEGATIVE effect (~3% decrease in task success)
- Developer-written files give only marginal gains (~4% increase)
- Architecture overviews "do not provide effective overviews"
- Long files increase costs by 20%+ and steps by 3+ on average
- Overexploration: too much architecture description causes agents to explore unnecessarily

### CLAUDE.md -- Claude Code's Native Format

**Features beyond AGENTS.md**:
- `@import` syntax for modular files
- Path-scoped rules via YAML frontmatter with globs
- Five-level hierarchy: global → project root → subdirectory (lazy-load) → path-scoped → personal
- Auto-memory: writes session notes to `~/.claude/projects/<name>/memory/`
- Hooks: deterministic actions (lint after every edit, block push without tests)
- `CLAUDE.local.md` for personal gitignored overrides

**Best practice**: Claude Code reads `AGENTS.md` as fallback when no `CLAUDE.md` is present. Many teams maintain both: `AGENTS.md` for universal rules, `CLAUDE.md` for Claude-specific enhancements. Symlink pattern: `ln -s AGENTS.md CLAUDE.md`.

**Critical constraint**: Keep under 200 lines. Over 200 lines, instruction-following degrades. Move automation rules to hooks, workflows to skills, shared chunks to `.claude/rules/` with `@import`.

### Cursor Rules (`.cursor/rules/*.mdc`)

- Uses `.mdc` (Markdown Cursor) files with YAML frontmatter
- Four rule types: Always Apply, Apply Intelligently (by description), Apply to Specific Files (by glob), Apply Manually (`@`-mention)
- Glob scoping: `src/**/*.tsx` activates rules only for matching files
- Legacy `.cursorrules` (single file) is deprecated in favor of `.cursor/rules/` directory
- Cursor also reads `AGENTS.md` natively

### GitHub Copilot Instructions (`.github/copilot-instructions.md`)

- Plain Markdown in `.github/` directory
- Three scopes: Personal (highest) > Repository > Organization
- Path-specific: `.github/instructions/*.instructions.md` with `applyTo` globs
- Also reads `AGENTS.md` natively
- Keep under two pages; move path-specific rules to `.github/instructions/`

### MCP Server Patterns for Domain Knowledge

**Key pattern**: Reference-by-handle. Store context in tools, hydrate via resources.

**Layered context architecture** (Microsoft MCP Best Practices):
1. **Core Layer**: Essential information always loaded (AGENTS.md)
2. **Situational Layer**: Context specific to current interaction
3. **Supporting Layer**: Additional context accessed when needed
4. **Fallback Layer**: Information accessed only on demand

**MCP Design for domain knowledge**:
- Tools for mutations (store, search, update context)
- Resources for reads (hydrate content on demand with token budgets)
- Progressive disclosure: return handles with summaries, hydrate full content only when needed

### Distro-Specific AI Tooling (Found)

1. **packit/ai-workflows** (Red Hat/RHEL): AI-powered RPM package maintenance using BeeAI framework + Vertex AI. Automates triage, rebase, backport, and release management for RHEL packages. Uses Claude Code skills (`agents_as_skills/`).

2. **Odilhao/packaging-skills** (Foreman/Katello/Pulp): AI agent skills for RPM packaging with obal, COPR, Koji. Uses AGENTS.md + skills directory + MCP server configs pattern.

3. **konflux-ci/rpmbuild-pipeline**: RPM build pipeline with Mock in containers, multi-arch support, SBOM generation. Not AI-driven but defines the build pipeline pattern.

4. **Azure Linux**: TOML-based declarative distro config with overlays applied to Fedora specs. Rendered specs checked in for auditability. Uses Copilot prompts in `.github/`.

5. **YAP (Yet Another Packager)**: Multi-format package builder that ships an MCP server (`yap-mcp`) so LLMs can drive package builds directly. Includes a SKILL.md for Claude Code/anthropic agents.

### Summary: What Works Across Platforms

| Mechanism | OpenCode | Claude Code | Cursor | Copilot | VSCode |
|-----------|----------|-------------|--------|---------|--------|
| `AGENTS.md` (root) | Yes | Yes (fallback) | Yes | Yes | Yes |
| `CLAUDE.md` (root) | No | Yes (native) | No | No | Yes (optional) |
| `.cursor/rules/*.mdc` | No | No | Yes (native) | No | No |
| `.github/copilot-instructions.md` | No | No | No | Yes (native) | Yes |
| MCP servers (tools/resources) | Yes | Yes | Yes | Partial | N/A |
| Skills (SKILL.md) | Yes | Yes | Partial | No | N/A |
| `@import` in context files | No | Yes | No | No | No |
| Subdirectory AGENTS.md | Yes | Yes | Yes | Yes | Yes |
| Path-scoped rules (globs) | No | Yes | Yes | Yes | Partial |
| Auto-memory | No (engram MCP) | Yes (built-in) | No | Yes (Copilot Memory) | No |

**The winning strategy**: `AGENTS.md` at repo root as single source of truth, with symlinks or tool-specific files for tool-only features. Skills for reusable workflows. MCP servers for live data access.

### Evolvable Configuration Patterns

1. **Layered Configuration** (from AI fleet management research):
   ```
   Global Defaults (Git-versioned, authoritative)
     └── Fleet/Environment Defaults
         └── Instance Overrides (tracked in git)
             └── Runtime Overrides (ephemeral)
   ```

2. **SchemaVer** (from Snowplow, via Zylos Research):
   - MODEL change: semantic meaning change (requires human approval)
   - REVISION change: new optional fields (backward-compatible)
   - ADDITION change: additive only (safe to auto-apply)

3. **GitOps as Delivery**: Agent config in Git → commit triggers validation → merge triggers deployment. Drift detection between declared and live state.

4. **Staged promotion**: Non-prod evaluation → approval gate → production. Never deploy agents directly without passing through staging.

5. **Version key in context files**: Include a version number (`context-version: "1"`) in AGENTS.md so agents can detect when the context format has changed.

---

## D. Knowledge Map

### What an Agent MUST Know (Stable Facts -- Anchored)

These change rarely or never:

| Knowledge | Source | Stability |
|-----------|--------|-----------|
| Maqui is an independent LFS-based distro with RPM/DNF5 + OpenRC | `docs/DISTRO-IDENTITY.md` | Permanent |
| Multiarch layout: `/usr/lib/x86_64-linux-gnu/` and `/usr/lib/i386-linux-gnu/` | `README.md` | Permanent |
| Gen3 spec conventions: debug disabled, release tag `1.m264`, library dirs | `SPECS/SPEC_TEMPLATE.md` | Release-bound |
| Overlayfs model: base (immutable) + upper (writable) + work | `lib/chroot.sh` | Permanent |
| Workspace bind mount at `/workspace` or `/mnt/workspace` inside chroot | `lib/chroot.sh` | Permanent |
| DNF5 local repo at `/mnt/repo` with `gpgcheck=0` | `lib/chroot.sh` | Until PGP phase |
| Language policy: ALL English, no emojis | `AGENTS.md` | Permanent |
| Specs are single source of truth for packages | `docs/DISTRO-IDENTITY.md` | Permanent |
| 7 self-hosting critical packages | `AGENTS.md` | Semi-stable |

### What an Agent MUST Know How to Do (Procedures)

These may evolve as tooling changes:

| Procedure | Current Implementation | Evolvability |
|-----------|----------------------|--------------|
| Build an RPM | `mql build <spec>` → `scripts/build-spec.sh` → `rpmbuild` in chroot | Medium -- `mql build` API is stable; underlying script may change |
| Install an RPM | `mql install <spec>` → `scripts/install-spec.sh` → `dnf install` | Medium -- DNF5 command format may change |
| Enter chroot | `mql chroot` (interactive) or `mql chroot --exec "<cmd>"` | High -- CLI may add flags |
| Mount/unmount overlay | `mql chroot --mount` / `--umount` | High -- may change |
| Fetch sources | `scripts/fetch-spec-sources.sh <spec>` | Medium |
| Update repo metadata | `mql repo update` → `createrepo_c` | Low -- may add signing |
| Sync to production repo | `mql repo sync` → `rsync` | High -- host/path configurable |
| Generate ISO | `mql release iso` | Medium -- may add flags |
| Test in QEMU | `mql test vm` | Medium |

### What Context Changes Over Time (Evolvable)

| Context | Change Trigger | Impact |
|---------|---------------|--------|
| `mql` CLI subcommands and flags | CLI refactors, new features | Agent commands break if not updated |
| Config file layout (`mql.conf`, `mql.local`) | Config refactoring | Path resolution changes |
| Build flags (`--skip-tests`, `--nodeps`) | Workflow changes | Build commands change |
| CI/CD workflow | Pipeline changes | Agent's understanding of "how to ship" changes |
| Chroot bind mount paths | Rootfs layout changes | Path references break |
| DNF5 repo config format | PGP implementation | `gpgcheck=0` removed |
| RPM release tag format | Version bumps (m264 → m265) | Spec authoring convention changes |
| Self-hosting package list | New packages added | Dependency graph changes |
| Documentation index | Docs restructured | Agent navigation paths change |
| Project repository URL / sync host | Infrastructure migration | `repo.glats.org` may change |

### What Context is Stable (Anchored)

These are foundational and unlikely to change:
- RPM as package format
- Spec files as package recipes
- Overlayfs approach to chroot management
- x86_64 + i686 architecture
- Multiarch library layout
- English-only policy
- Spec-driven development philosophy
- `docs/DISTRO-IDENTITY.md` as canonical definition

---

## E. Proposed Stack Architecture (Initial Sketch)

### Design Principles

1. **Single source of truth**: One canonical file per concept; symlink for cross-tool compatibility
2. **Progressive disclosure**: Short root file; details in referenced documents loaded on demand
3. **Evolvability by design**: Regenerable files for volatile context; version key for format changes
4. **Minimal viable first**: Start with AGENTS.md + agent_docs/; add skills and MCP later
5. **Portable across tools**: AGENTS.md for all tools; tool-specific files only for tool-unique features

### Artifact Inventory

```
maquilinux/
├── AGENTS.md                          # Cross-tool entry point (150-200 lines max)
├── CLAUDE.md → AGENTS.md              # Symlink for Claude Code compatibility
├── agent_docs/                        # Domain-specific reference (loaded on demand)
│   ├── distro-identity.md             # What Maqui IS (stable, from docs/DISTRO-IDENTITY.md)
│   ├── build-workflow.md              # Step-by-step build procedure (semi-stable)
│   ├── spec-conventions.md            # Gen3 spec format rules (stable per release)
│   ├── chroot-model.md                # Overlay system architecture (stable)
│   ├── mql-cli-reference.md           # Complete command reference (REGENERABLE)
│   ├── common-gotchas.md              # Known failure modes and recovery (evolvable)
│   └── multiarch-guide.md             # i686 conditional patterns (stable)
├── .opencode/
│   └── skills/
│       └── maqui-build/               # OpenCode skill for package building
│           └── SKILL.md               # Build workflow: create spec → fetch → build → install → repo update
├── .claude/
│   └── rules/
│       └── maqui-conventions.md       # Claude Code path-scoped rules (optional)
└── .github/
    └── copilot-instructions.md        # Copilot-specific (TBD if needed, may just reference AGENTS.md)
```

### Layer 0: `AGENTS.md` (Root -- Cross-Tool Standard)

**Purpose**: The entry point every AI agent reads first. Must be under 200 lines (budget constraint). Contains:
1. Project identity: one-paragraph summary of what Maqui is
2. Quick reference: most common commands (build, install, chroot)
3. Key constraints: English-only, no emojis, spec conventions
4. Critical gotchas: overlay mount requirements, --nogpgcheck, promote confirmation
5. Knowledge index: pointer to `agent_docs/` with one-line descriptions
6. Context version: `agent-context-version: "1"` (for evolvability detection)

What it does NOT contain:
- Architecture explanations (point to agent_docs/)
- Full CLI reference (point to agent_docs/mql-cli-reference.md)
- Spec format details (point to agent_docs/spec-conventions.md)
- Build step-by-step (point to agent_docs/build-workflow.md)

### Layer 1: `agent_docs/` (Domain Reference -- On-Demand)

Each file is under 100 lines, focused on one domain. Agents load these when working in that domain.

| File | Content | Regenerable? | Stability |
|------|---------|-------------|-----------|
| `distro-identity.md` | What Maqui is, characteristics, versioning, branding | No (manual) | High |
| `build-workflow.md` | Step-by-step from spec to RPM, flags, scripts | Partially (commands) | Medium |
| `spec-conventions.md` | Gen3 format, release tag, multiarch patterns, %files | No (manual) | High (release-bound) |
| `chroot-model.md` | Overlayfs layers, bind mounts, virtual FS, repo config | No (manual) | High |
| `mql-cli-reference.md` | Full command listing with examples and flags | YES (generated from `mql --help`) | Low (volatile) |
| `common-gotchas.md` | Known failure modes, recovery procedures, stale mounts | No (manual, append-only) | Medium |
| `multiarch-guide.md` | i686 conditional patterns, library dirs, ExclusiveArch | No (manual) | High |

### Layer 2: Skills (OpenCode-Specific, Reusable)

**Skill: `maqui-build`** (`.opencode/skills/maqui-build/SKILL.md`)
- **Trigger**: "build RPM", "build spec", "create package", "mql build"
- **What it does**: Walks agent through the complete build workflow
  1. Check spec exists at `SPECS/<name>.spec`
  2. Verify sources present in `SOURCES/`
  3. Ensure overlay is mounted (`mql chroot --mount`)
  4. Run `mql build <spec>` with appropriate flags
  5. If successful, run `mql repo update`
  6. Optionally install: `mql install <spec>`
- **Reference files**: agent_docs/build-workflow.md, agent_docs/spec-conventions.md

**Skill: `maqui-spec-create`** (`.opencode/skills/maqui-spec-create/SKILL.md`)
- **Trigger**: "create spec", "new spec", "write spec for", "package X"
- **What it does**: Guides agent through spec creation following Gen3 conventions
  1. Identify upstream version and source URL
  2. Create spec with proper Name, Version, Release (1.m264)
  3. Add debug_package disabled boilerplate
  4. Determine BuildRequires from configure/meson/cmake
  5. Write %prep, %build, %install, %files sections
  6. Add multiarch conditionals if library package
- **Reference files**: agent_docs/spec-conventions.md, agent_docs/multiarch-guide.md

### Layer 3: MCP Server (Future -- Phase 2+)

A `maqui-build` MCP server that exposes:
- **Tools**: `build_package(spec_name, arch, skip_tests)`, `install_package(spec_name)`, `update_repo()`, `check_sources(spec_name)`, `mount_chroot()`, `umount_chroot()`, `get_build_status(spec_name)`, `list_available_specs()`
- **Resources**: `maqui://specs/{name}/info` (spec metadata), `maqui://rpms/{arch}/` (built RPMs), `maqui://chroot/status` (overlay state)

This would be a Phase 2 enhancement after the AGENTS.md + agent_docs stack is validated. Benefits: token efficiency (tools return structured data, not chat context), runtime validation (check actual state), cross-tool compatibility (any MCP client can use it).

### Platform Coverage Matrix

| Platform | AGENTS.md | agent_docs/ | Skills (.opencode/) | Skills (.claude/) | MCP Server |
|----------|-----------|-------------|---------------------|-------------------|------------|
| **OpenCode** | Yes | Manual load | Yes | No (unless configured) | Yes |
| **Claude Code** | Yes (via CLAUDE.md symlink) | Manual load | No | Yes (if moved) | Yes |
| **VSCode (Copilot)** | Yes | Manual load | No | No | Yes (if configured) |
| **Cursor** | Yes | Manual load | No | No | Partial |
| **Aider** | Yes | Manual load | No | No | Partial |
| **Codex CLI** | Yes | Manual load | No | No | Yes |

### Evolvability Strategy

**Principle**: Treat agent context like infrastructure-as-code. Version it, review it, regenerate it when source changes.

1. **Version key**: Include `context-version: "N"` in AGENTS.md. When format changes, bump the version. Agents check this to detect stale context.

2. **Regenerable files**: `mql-cli-reference.md` is regenerated from `mql --help` output. When the CLI changes, regenerate the reference. Could be a pre-commit hook or CI check.

3. **Git hooks**: A pre-commit hook (`scripts/check-agent-context.sh`) that:
   - Validates AGENTS.md is under 200 lines
   - Checks that regenerated files are up to date
   - Warns if agent_docs/ files reference paths that no longer exist

4. **CI validation**: A GitHub Actions workflow that:
   - Runs `mql --help` and diffs against `agent_docs/mql-cli-reference.md`
   - Checks that all paths referenced in agent_docs/ actually exist in the repo
   - Validates AGENTS.md doesn't exceed line budget

5. **Review gates**: Changes to agent_docs/ are reviewed alongside the code changes that triggered them. If you change `mql build` flags, update `agent_docs/build-workflow.md` in the same PR.

6. **Progressive disclosure by design**: Root AGENTS.md stays short (under 200 lines). New context is added to the appropriate agent_docs/ file, not the root. Files are loaded on demand by the agent, not auto-included.

7. **Symlink strategy**: `CLAUDE.md → AGENTS.md` for Claude Code. If Cursor-specific scoped rules are needed later, add `.cursor/rules/` but keep shared rules in AGENTS.md.

8. **When to split**: When agent_docs/ has files consistently unused by agents (measured by observing agent sessions), those files become candidates for removal or de-prioritization.

9. **Post-upgrade validation**: After updating the agent context stack, test with a fresh agent session: "build package X" and verify the agent follows the new instructions without stumbling.

10. **Memorialized in AGENTS.md itself**: The AGENTS.md file includes a section explaining the context stack structure, so future agents (and humans) understand how the system works.

---

## Key Discoveries

1. **AGENTS.md is the clear cross-tool standard**: 60+ tools, Linux Foundation governance. Claude Code reads it as fallback. Cursor and Copilot read it natively. This is the anchor artifact.

2. **AGENTS.md must be under 200 lines**: Research shows instruction-following degrades past this threshold. The root file should be a lean entry point, not a comprehensive manual.

3. **Architecture overviews don't help agents**: The ETH Zurich study (2026) found removing architecture sections while keeping commands, constraints, and gotchas produces the same agent behavior at lower token cost.

4. **`@import` is Claude Code-only**: Modularization via imports works in Claude Code but not in OpenCode or other tools. Keep shared context in plain markdown files that any agent can read.

5. **Skills are portable across OpenCode and Claude Code**: Both support the `SKILL.md` format (Anthropic Agent Skills Specification). Skills placed in `.opencode/skills/` work for OpenCode; `.claude/skills/` works for Claude Code.

6. **NixOS declarative config is NOT suitable for project-specific agent context**: The current `~/.nixos/shared/opencode.nix` manages global config. Project-specific agent context (AGENTS.md, agent_docs/) should live in the Maqui Linux repo and be version-controlled there, not in NixOS config.

7. **MCP server for builds is the endgame but AGENTS.md is the start**: An MCP server gives the most powerful integration (structured tool calls, runtime state validation), but AGENTS.md + agent_docs/ gives 80% of the value with 20% of the effort. Start with files, add MCP later.

8. **Regenerable context is the key to evolvability**: Volatile context (CLI flags, paths) should be regenerated from source-of-truth (`mql --help`, directory listing), not maintained manually. This prevents drift.

9. **Precedent exists in RPM packaging AI tooling**: packit/ai-workflows (Red Hat), packaging-skills (Foreman), and YAP MCP server all demonstrate patterns for AI-driven RPM workflows. Maqui can learn from these.

10. **Dual GitHub MCP auth is project-specific but configured globally**: The `github-personal` and `github-work` MCP servers are configured in `~/.config/opencode/opencode.json`. For project-specific GitHub operations, this is sufficient since the repo is on GitHub.

---

## Affected Areas

- `AGENTS.md` -- will be rewritten as lean entry point with context version and pointer index
- `agent_docs/` -- new directory with 7 reference files
- `.opencode/skills/maqui-build/` -- new project-level skill
- `.opencode/skills/maqui-spec-create/` -- new project-level skill
- `CLAUDE.md` -- new symlink to AGENTS.md
- `docs/DISTRO-IDENTITY.md` -- exists; content duplicated/normalized into agent_docs/distro-identity.md (or pointer from AGENTS.md)
- `scripts/` -- potential pre-commit hook for context validation
- `.github/workflows/` -- potential CI check for context freshness

---

## Ready for Proposal

Yes. The exploration is complete. Key decisions for the proposal phase:

1. **Start with AGENTS.md + agent_docs/ only** (Phase 1, immediate). Skills and MCP server are Phase 2+.
2. **Keep AGENTS.md under 200 lines** as a hard budget constraint.
3. **Use `agent-context-version: "1"`** in AGENTS.md for evolvability.
4. **Symlink CLAUDE.md → AGENTS.md** for Claude Code compatibility.
5. **Place project skills in `.opencode/skills/`** (not `.claude/skills/`) since OpenCode is the primary agent.
6. **Regenerate `mql-cli-reference.md`** from `mql --help` output for the initial version.
7. **Defer `.cursor/rules/` and `.github/copilot-instructions.md`** until there is evidence those tools are being used with this project.

The orchestrator should proceed to **proposal** phase with these findings.

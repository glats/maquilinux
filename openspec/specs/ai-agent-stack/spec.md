# AI Agent Context Stack Specification

## Purpose

Define the 9 cross-tool agent context files that enable AI tools (OpenCode, Claude Code, VSCode/Copilot, Cursor) to perform spec-driven RPM development on Maqui Linux. Phase 1 delivers a progressive-disclosure architecture: AGENTS.md (always loaded) + agent_docs/ (on-demand).

## Requirements

### R.1: AGENTS.md (Rewrite)

AGENTS.md MUST be 150-200 line plain Markdown entry point. MUST contain: project identity (one paragraph), `agent-context-version: "1"` marker, critical gotchas (max 6 items), agent_docs/ index with one-line descriptions. MUST NOT contain: architecture explanations, full CLI reference, spec format details, build step-by-step, emojis. Source: current `AGENTS.md`, `docs/DISTRO-IDENTITY.md`. Cross-tool: plain Markdown read natively by all tools. Evolvability: evolvable (budget-limited). Verify: `wc -l AGENTS.md` yields 150-200; first non-comment line is version marker; doc index entries resolve to existing files.

### R.2: CLAUDE.md (Symlink)

MUST be POSIX symlink to `AGENTS.md`. MUST NOT be separate file. Source: `ln -s`. Cross-tool: Claude Code native; POSIX standard. Evolvability: stable. Verify: `readlink CLAUDE.md` returns `AGENTS.md`.

### R.3: agent_docs/distro-identity.md

MUST describe: independent LFS-based distro, RPM+DNF5+OpenRC, x86_64+i686, multiarch lib layout, specs as source of truth, YY.MM versioning, branding. Max 60 lines. MUST NOT contain build commands or troubleshooting. Source: `docs/DISTRO-IDENTITY.md`. Evolvability: stable. Verify: matches facts in DISTRO-IDENTITY.md; contains characteristics table.

### R.4: agent_docs/build-workflow.md

MUST document 6-step pipeline: spec creation, source fetching, overlay mount, build, install, repo update. Each step: exact mql command, flags, and verification. Max 80 lines. MUST NOT contain architecture theory or troubleshooting (defer to R.9). Source: `scripts/build-spec.sh`, `scripts/install-spec.sh`. Evolvability: mostly-stable. Verify: `mql build`, `mql install`, `mql repo update` documented with flags.

### R.5: agent_docs/spec-conventions.md

MUST document: debug_package disabled, release tag `1.m264`, lib dirs (`/usr/lib/x86_64-linux-gnu/` and `/usr/lib/i386-linux-gnu/`), `%if "%{_target_cpu}" == "i686"` conditionals, `ExclusiveArch`, BuildRequires. Max 80 lines. MUST NOT contain build commands or chroot details. Source: `SPECS/SPEC_TEMPLATE.md`. Evolvability: mostly-stable (release-bound). Verify: matches SPEC_TEMPLATE.md conventions.

### R.6: agent_docs/chroot-lifecycle.md

MUST document: overlayfs (base/upper/work layers), bind mounts (workspace at `/mnt/workspace`, RPMS at `/mnt/repo`), virtual FS, mount/unmount, reset, persist, promote (interactive confirmation), stale mount recovery. Max 80 lines. MUST NOT contain spec conventions or build workflow. Source: `lib/chroot.sh`. Evolvability: stable. Verify: overlay layer model present; promote confirmation requirement documented.

### R.7: agent_docs/dependency-resolution.md

MUST document: BuildRequires chain analysis, build order from dependency graph, dnf install with `--nogpgcheck` from local repo, `--nodeps` flag, `--both` multiarch implications. Max 70 lines. MUST NOT contain general build workflow or troubleshooting. Source: `scripts/build-spec.sh`, `scripts/install-spec.sh`. Evolvability: mostly-stable (DNF5 command may change). Verify: build order determination described; dnf install command documented with correct repo path.

### R.9: agent_docs/troubleshooting.md

MUST document failure modes and recovery: overlay not mounted, source not found, BuildRequires unresolved, i686 detection, stale mounts after crash, promote confirmation, GPG errors, workspace bind mount missing. Max 80 lines. Each entry: command to diagnose + command to fix. Source: `AGENTS.md` gotchas, `lib/chroot.sh`. Evolvability: evolvable (append-only). Verify: covers all failure modes from exploration.md; each mode has diagnostic and fix commands.

## Global Scenarios

### Scenario: Agent Onboarding
- GIVEN agent with no Maqui knowledge opens project
- WHEN agent reads `AGENTS.md`
- THEN agent identifies distro type, locates `build-workflow.md` for build tasks, knows version marker exists

### Scenario: Cross-Tool Compatibility
- GIVEN `AGENTS.md` opened by any of OpenCode, Claude Code, Cursor, Copilot
- WHEN parsed as plain Markdown
- THEN no tool-specific syntax present (`@import`, YAML frontmatter, `.mdc`)
- AND CLAUDE.md symlink provides Claude Code native entry

### Scenario: Layered Loading
- GIVEN agent asked to build a package
- WHEN loading context
- THEN loads: AGENTS.md -> build-workflow.md -> spec-conventions.md -> dependency-resolution.md
- AND does NOT load distro-identity.md or troubleshooting.md
- AND loads troubleshooting.md only on build failure

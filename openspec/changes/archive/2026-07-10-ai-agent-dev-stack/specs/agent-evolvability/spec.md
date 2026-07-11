# Agent Evolvability Specification

## Purpose

Define the mechanisms that keep the AI Agent Context Stack aligned with the evolving Maqui Linux distribution. This spec covers version detection, regenerable artifacts, progressive disclosure architecture, and stability classification.

## Requirements

### R.8: agent_docs/mql-cli-reference.md (Regenerable)

MUST contain complete `mql` command reference: all subcommands (`chroot`, `build`, `install`, `backup`, `repo`, `release`, `test`, `config`) with their flags and usage examples. MUST be regenerate from `mql --help` output (single source of truth). Max 100 lines. MUST NOT contain: implementation details, script internals, or manually-maintained flag lists when automation can produce them. Source of truth: `mql --help` output from Nix dev shell or standalone environment. Compatible: plain Markdown readable by all tools. Evolvability class: evolvable (regenerated on CLI change). Verify: `mql --help` output matches documented flags; every documented subcommand exists in `mql --help`; no flag listed that does not appear in `mql --help`.

### R.E1: Context Version Marker

AGENTS.md MUST include `agent-context-version: "1"` as its first non-comment line. When the context stack format changes (file renames, new required files, structural reorganization), this version SHALL be incremented. Agents MAY check this marker against their cached context to detect staleness. Verify: `head -1 AGENTS.md` returns the version marker; version is an integer string.

### R.E2: Progressive Disclosure Architecture

The context stack MUST follow a three-layer loading model: Layer 0 (AGENTS.md, always loaded, 150-200 lines), Layer 1 (agent_docs/ files, loaded on demand per task domain), Layer 2 (skills and MCP, Phase 2+). AGENTS.md MUST NOT inline content that belongs in Layer 1. Each agent_docs/ file MUST be self-contained for its domain. Verify: AGENTS.md is under 200 lines; each agent_docs/ file is under its line budget; no redundant content exists across files.

### R.E3: Stability Classification

Each agent_docs/ file MUST be annotated with its stability class at the top of the file. Classes: Stable (rarely changes), Mostly-Stable (tied to release cycle), Evolvable (changes with tooling or experience). Assignments: distro-identity (Stable), chroot-lifecycle (Stable), spec-conventions (Mostly-Stable), build-workflow (Mostly-Stable), dependency-resolution (Mostly-Stable), mql-cli-reference (Evolvable), troubleshooting (Evolvable). Verify: `grep -l "Stability:" agent_docs/*.md` returns all 7 files; no file uses an undefined stability class.

### R.E4: Regeneration Contract

agent_docs/mql-cli-reference.md SHALL be regenerable from `mql --help` by a deterministic script. The regeneration command SHALL be documented in the file header. When `mql --help` output changes (CLI refactors, new flags), regenerating the reference file and committing the result with the CLI change SHALL be part of the change's acceptance criteria. Verify: regeneration command exists and is documented; regenerated output is identical to committed file (bit-for-bit or semantically equivalent).

## Global Scenarios

### Scenario: Evolvability Detection

- GIVEN an agent previously cached context with `agent-context-version: "1"`
- WHEN the agent re-opens the project and reads `AGENTS.md`
- AND the version marker is now `"2"`
- THEN the agent detects stale context
- AND the agent re-reads `AGENTS.md` and the agent_docs/ index to discover new or renamed files

### Scenario: CLI Reference Regeneration

- GIVEN `mql build` gains a new flag `--verify-checksums`
- WHEN `mql --help` output is updated
- THEN regenerating `agent_docs/mql-cli-reference.md` captures the new flag
- AND the documentation matches the CLI behavior without manual editing
- AND the commit containing the CLI change also includes the regenerated reference file

### Scenario: Stability-Guided Maintenance

- GIVEN a developer changes the overlay promote mechanism
- WHEN the developer checks agent_docs/ files for affected docs
- THEN `chroot-lifecycle.md` (Stable) requires review for accuracy
- AND `troubleshooting.md` (Evolvable) may need a new failure mode entry
- AND `distro-identity.md` (Stable) is unaffected

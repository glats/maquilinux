# ADR-003: Remove LFS Branding References from Maqui Linux

## Status

Proposed

## Context

Maqui Linux originated from following the Linux From Scratch (LFS) and Multilib
Linux From Scratch (MLFS) build instructions. During early development, many
references to "Linux From Scratch", "LFS", and "MLFS" were incorporated into:

- Configuration variables (`MQL_LFS` - the mount point for the development rootfs)
- Documentation describing the project's origins
- Script names (`mlfs-runner.sh`, `cleanup-lfs-remnants.sh`)
- Comments and internal terminology ("LFS bootstrap", "LFS vestiges", "LFS-era")

As the project has evolved into an independent Linux distribution with its own:
- RPM + DNF5 package management (not LFS tarball-based)
- OpenRC init system (not LFS SysVinit)
- Custom dracut-based initramfs
- Self-hosted build infrastructure
- Independent release cycle

...the continued use of "LFS" branding creates confusion about the project's
identity and implies it remains merely a derivative of LFS rather than an
independent distribution.

**Current state:** 268+ references to "LFS" or "Linux From Scratch" found across
22+ files, categorized as:
1. Configuration variable `MQL_LFS` (104+ occurrences)
2. Documentation branding ("Linux From Scratch" in README, AGENTS.md, etc.)
3. Script naming (`mlfs-runner.sh`, `cleanup-lfs-remnants.sh`)
4. Historical/contextual references ("LFS bootstrap", "LFS vestiges")

## Alternatives Considered

| Option | Description | Pros | Cons | Rejected because |
|--------|-------------|------|------|-----------------|
| **Keep all LFS references** | Maintain all "LFS" and "Linux From Scratch" text | Acknowledges historical origins | Weakens independent brand; creates confusion with LFS project; implies subordinate status | Would prevent establishing Maqui Linux as its own distribution brand |
| **Remove everything including history** | Strip all LFS/MLFS text including spec changelogs | Cleanest branding separation | Loses provenance documentation for packages; hides legitimate lineage | Historical record has value; misleading to hide origins completely |
| **Remove branding, keep history (chosen)** | Remove branding references but keep historical notes | Best of both: clean brand + honest history | Requires careful distinction between branding and history; more work | Acceptable trade-off - provides independent identity while acknowledging origins |

## Decision

We will remove all "Linux From Scratch" and "LFS" **branding** references while
preserving **historical** references that document package lineage.

### What constitutes branding (to be removed):
- "Linux From Scratch" in project description
- `MQL_LFS` configuration variable (replaced with `MQL_ROOT`)
- "LFS bootstrap", "LFS vestiges", "LFS-era" terminology (replaced with "bootstrap")
- Script names `mlfs-runner.sh`, `cleanup-lfs-remnants.sh` (renamed to `maqui-runner.sh`, `cleanup-bootstrap-remnants.sh`)

### What constitutes history (to be preserved):
- RPM spec file changelogs mentioning "MLFS" (documents how package was originally built)
- Generic phrases like "build from scratch" (common English idiom, not LFS-specific)
- Technical explanations mentioning LFS as background context (when historically relevant)

### Implementation approach

**Phase 1: Configuration variable rename**
- Add `MQL_ROOT` as primary variable
- Keep `MQL_LFS` as deprecated fallback with warning
- Rename `get_lfs_path()` to `get_root_path()` with alias for backward compatibility
- Update all scripts to use `MQL_ROOT` with fallback to `MQL_LFS`

**Phase 2: Script renaming**
- `mlfs-runner.sh` → `maqui-runner.sh`
- `cleanup-lfs-remnants.sh` → `cleanup-bootstrap-remnants.sh`
- Update all references in documentation and other scripts

**Phase 3: Documentation updates**
- Remove "Linux From Scratch" from project descriptions
- Replace "LFS bootstrap"/"vestiges" with "bootstrap"
- Keep acknowledgments of origins where appropriate

**Phase 4: Removal of deprecated fallback**
- After transition period (3-6 months), remove `MQL_LFS` support
- Keep only `MQL_ROOT` going forward

## Consequences

### Positive

1. **Independent brand identity**: Maqui Linux establishes itself as a distinct distribution, not an LFS derivative.
2. **Reduced confusion**: Users won't mistake Maqui Linux for an LFS tutorial project.
3. **Professional perception**: Independent branding signals production-ready status.
4. **Flexibility**: Decouples project from LFS naming conventions and release schedules.
5. **Backward compatibility**: Transition period allows existing configurations to continue working.

### Negative

1. **Breaking change (mitigated)**: Existing user configs with `MQL_LFS` need migration - addressed via deprecation warnings and fallback.
2. **Documentation churn**: All guides and READMEs need updates - one-time effort.
3. **Potential confusion during transition**: Users may see both `MQL_LFS` and `MQL_ROOT` - addressed via clear deprecation messages.
4. **Effort required**: 268+ references across 22+ files need systematic updates.

## Implementation Details

### Files requiring changes by category:

| Category | Files | Specific Changes |
|----------|-------|-----------------|
| CLI Core | `mql` | Replace `MQL_LFS` with `MQL_ROOT` (12 occurrences) |
| Config | `mql.local.example` | Update example configurations |
| Library | `lib/common.sh` | Rename `get_lfs_path()` → `get_root_path()` + alias |
| Library | `lib/backup.sh` | Update function calls |
| Scripts | `scripts/run-in-chroot.sh` | Update variable references |
| Scripts | `scripts/setup-runner.sh` | Update generated config |
| Scripts | `scripts/enter-chroot.sh` | Update variable references |
| Scripts | `scripts/enter-chroot-build.sh` | Update variable references |
| Scripts | `scripts/build-spec.sh` | Update variable references |
| Scripts | `scripts/install-spec.sh` | Update variable references |
| Scripts | `scripts/mlfs-runner.sh` | Rename to `maqui-runner.sh` |
| Tools | `tools/cleanup-lfs-remnants.sh` | Rename to `cleanup-bootstrap-remnants.sh` |
| Documentation | `README.md` | Remove LFS description |
| Documentation | `AGENTS.md` | Remove "based on Linux From Scratch" |
| Documentation | `docs/DEVELOPMENT-SYSTEM-PLAN.md` | Remove LFS base reference |
| Documentation | `docs/GETTING-STARTED.md` | Update 20+ MQL_LFS references |
| Documentation | `docs/MANUAL-NIX.md` | Update MQL_LFS references |
| Documentation | `docs/MANUAL-STANDALONE.md` | Update MQL_LFS references |
| Documentation | `docs/agents/standalone-developer.md` | Update MQL_LFS references |
| Documentation | `docs/agents/runner-setup.md` | Update MQL_LFS references |
| Documentation | `docs/DEVELOPMENT.md` | Update script name references |
| Nix | `flake.nix` | Update variable references |

### Backward compatibility strategy

```bash
# In lib/common.sh - primary function with fallback
get_root_path() {
    echo "${MQL_ROOT:-${MQL_LFS:-/mnt/maquilinux}}"
}

# Deprecated alias for compatibility
get_lfs_path() {
    get_root_path
}

# In mql - warning if using deprecated variable
if [[ -n "${MQL_LFS:-}" && -z "${MQL_ROOT:-}" ]]; then
    log_warn "MQL_LFS is deprecated. Please use MQL_ROOT."
    MQL_ROOT="$MQL_LFS"
fi
```

## Compliance with Decision Framework

This ADR follows the project's decision-framework checklist:

- **Research**: Explored all 268+ references across the codebase; categorized as branding vs history
- **Alternatives**: Compared three approaches (keep all, remove all, selective removal)
- **Maintenance**: Transition strategy preserves working configurations during migration
- **Dependencies**: No new dependencies introduced; pure refactoring
- **Compatibility**: Backward compatibility layer ensures smooth transition
- **Self-hosting impact**: No impact on self-hosting capability; purely cosmetic/naming changes
- **Long-term fit**: Establishes independent brand appropriate for distribution maturity

## References

- Exploration analysis: `sdd/remove-lfs-references/proposal` (Engram)
- LFS project: https://www.linuxfromscratch.org/
- Maqui Linux project identity requirements
- Existing ADR-001, ADR-002 for format reference

## Notes

- The term "MLFS" in RPM spec changelogs is **preserved** - it documents the
  build origin of packages and is not branding.
- Generic phrases "from scratch" are **preserved** - they are common English
  idioms predating the LFS project.
- Backward compatibility will be maintained for **3-6 months** before removing
  `MQL_LFS` support entirely.

---

*Created: 2026-04-19*  
*Last updated: 2026-04-19*  
*Status: Proposed*

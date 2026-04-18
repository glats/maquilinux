# ADR-002-EXPLORATION: Build System Options for Maqui Linux

## Status

**Exploration / Discussion** — Documenting options, no decision made

## Context

Maqui Linux is a self-hosted RPM-based distribution (x86_64/i686 multilib). We need to design a build system that can handle:

1. **Dependency cascades**: When a library changes, dependents need rebuilds
2. **Current resources**: 1 runner (thinkcentre.local), 1 developer
3. **Target**: Reach XFCE/MATE desktop (50-100 packages with complex deps)
4. **Special cases**: 3-hour Rust bootstrap, kernel builds, ISO generation

This document explores options without committing to one yet.

## Options Under Consideration

### Option A: Koji-style (Fedora model)

**Architecture**:
```
koji-hub (coordinator) ─┬─→ kojid-builder-1
                       ├─→ kojid-builder-2  
                       └─→ kojid-builder-N
```

**Components**:
- PostgreSQL database
- XML-RPC hub
- Web interface (koji-web)
- Builder daemons (kojid)
- Mock for chroots
- Tags and targets for dependency chains

**Pros**:
- Handles complex dependency chains via tags
- Built for RPM
- Scales to hundreds of builders

**Cons**:
- Requires database + web server + multiple daemons
- Complex setup and maintenance
- Overkill for 1-2 runners
- Heavy operational burden

**Questions**:
- Do we want to operate a database just for builds?
- Is the complexity justified at our scale?

---

### Option B: Void-style (xbps-src inspired)

**Architecture**:
```
mql build <spec>
    ↓
Check dependencies (local→remote→source)
    ↓
Build in chroot (overlay)
    ↓
Detect reverse-deps (cascade)
    ↓
Rebuild dependents
```

**Key features**:
- Single script (`mql`) orchestrates
- Chroot-based builds (overlay system we have)
- Recursive dependency resolution
- GitHub Actions calls `mql` commands

**Pros**:
- Simple, understandable, modifiable
- Works with 1 runner (current situation)
- Uses our existing overlay chroot
- Easy to debug (just shell scripts)

**Cons**:
- Sequential by default
- Cascade detection needs scanning all specs
- No built-in distributed build support

**Questions**:
- Can we add parallelism later without rewriting?
- How to track reverse dependencies efficiently?

---

### Option C: Alpine-style (abuild model)

**Architecture**:
- APKBUILD format (different from RPM)
- Subpackages: doc, dev split automatically
- abuild command handles build + deps

**Pros**:
- Very simple templates
- Well-documented
- Automatic subpackage handling

**Cons**:
- Requires migration from RPM to APK
- Would lose DNF5 investment
- Different package manager ecosystem

**Questions**:
- Is the migration cost worth it?
- Do we want to abandon RPM?

---

### Option D: Hybrid GitHub Actions (workflow-based)

**Architecture**:
```yaml
jobs:
  resolve-deps:
    outputs: build_queue_json
  build:
    strategy:
      matrix: ${{ fromJson(needs.resolve.outputs.queue) }}
```

**Key features**:
- Dependency graph in JSON
- GitHub Actions matrix for parallelism
- Workflow visible in GitHub UI

**Pros**:
- Built-in parallelism when we have multiple runners
- Good visibility (GitHub UI shows progress)
- No daemon to maintain

**Cons**:
- Harder to test/debug locally
- YAML-heavy configuration
- Dependent on GitHub Actions platform

**Questions**:
- Can we run this locally for testing?
- What if we need to move off GitHub later?

---

## Decision Criteria (Weights TBD)

| Criterion | Option A | Option B | Option C | Option D |
|-----------|----------|----------|----------|----------|
| Complexity | High | Low | Medium | Medium |
| Works with 1 runner | No | Yes | Yes | Yes |
| RPM compatible | Yes | Yes | No | Yes |
| Parallel builds | Yes | No | No | Yes |
| Debuggable locally | No | Yes | Yes | Partial |
| Bootstrap support | Yes | Yes | Yes | Yes |
| Future scaling | High | Medium | Medium | High |

## Open Questions

1. **Do we need parallelism now?**
   - Current: 1 runner, sequential OK
   - Future: 3+ runners, want parallel

2. **How to handle cascade rebuilds?**
   - Option: `mql cascade <spec>` scans and rebuilds
   - Option: Dependency graph in separate file
   - Option: Dynamic detection via rpm -qR

3. **GitHub Actions lock-in?**
   - Current: Hosted on GitHub, using Actions
   - Future: Might want self-hosted GitLab or pure local

4. **Package count scale?**
   - Current: ~140 specs
   - Target (XFCE): ~200-300 specs
   - Full desktop: ~500+ specs

## Next Steps

**Before deciding, we need to**:

1. **Prototype Option B** (Void-style):
   - Implement `mql cascade` command
   - Test with a small dependency chain
   - Measure time for 5-10 package cascade

2. **Test Option D feasibility**:
   - Can we generate JSON dependency graph?
   - Test with GitHub Actions matrix
   - Check if it works with 1 runner (sequential fallback)

3. **Evaluate complexity**:
   - Try to setup minimal Koji locally (test complexity)
   - Compare maintenance burden

4. **Decide based on**:
   - Prototype results
   - Actual pain points encountered
   - Time to XFCE/MATE working

## References

- [Void Linux xbps-src](https://github.com/void-linux/void-packages)
- [Fedora Koji](https://fedoraproject.org/wiki/Koji)
- [Alpine abuild](https://wiki.alpinelinux.org/wiki/Creating_an_Alpine_package)
- [Arch makepkg](https://wiki.archlinux.org/title/Makepkg)

## Related Documents

- ADR-001: Build Dependency System (exploratory)
- Current runner: thinkcentre.local (1 machine, 2 cores)
- Target desktop: XFCE or MATE

---

**Created**: 2026-04-18  
**Status**: Exploration — no decision made  
**Next Review**: After prototyping Option B (mql cascade)

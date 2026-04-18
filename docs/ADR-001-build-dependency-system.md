# ADR-001: Build Dependency System for Maqui Linux

## Status
Proposed

## Context
Maqui Linux is a self-hosted RPM-based distribution built from source using `rpmbuild` inside a chroot environment. Currently, building packages is a manual process:

- Developers run `mql build <spec>` for each package individually
- No automatic dependency tracking between packages
- When a core package changes (e.g., glibc, gcc), dependent packages need to be rebuilt manually
- Build order is determined by human intuition and tribal knowledge
- This becomes unsustainable as the package count grows (currently 100+ spec files)

The current `mql build` command wraps `scripts/build-spec.sh`, which calls `rpmbuild` with appropriate macro overrides to use the Maqui Linux toolchain. Each spec file contains `BuildRequires:` and `Requires:` metadata, but this is used only at install time inside the chroot, not for scheduling builds.

**Pain points:**
1. After updating glibc, developers must manually identify and rebuild all packages that link against it.
2. No way to automatically rebuild a package's reverse dependencies (`mql rebuild <spec>`).
3. Builds are sequential even when independent packages could be built in parallel.
4. No persistent record of which packages depend on which others, making onboarding difficult.

## Alternatives Considered

| Option | Description | Pros | Cons | Rejected because |
|--------|-------------|------|------|-----------------|
| **Full RPM dependency solver** | Use `dnf5` or `rpm` to query `BuildRequires:` from spec files and compute build order dynamically. | Accurate; no manual file maintenance; captures conditional deps. | Requires RPM DB of all installed packages; spec files must be parseable outside chroot; complex to implement. | Overkill for initial phase; we need a simple solution now. |
| **Makefile with explicit rules** | Write a Makefile where each target is a spec and dependencies are expressed as Make prerequisites. | Leverages Make's built‑in parallelism and dependency resolution. | Makefiles become large (100+ targets); hard to maintain; not integrated with `mql`. | Doesn't fit the existing CLI workflow; would duplicate `mql build` logic. |
| **Graph database** | Store dependency graph in SQLite or Neo4j and provide queries for rebuild ordering. | Powerful queries; scalable to thousands of packages. | Heavyweight; introduces new runtime dependencies; over‑engineering. | We have <200 packages; a text file is sufficient. |
| **No dependency tracking** | Continue manual builds; rely on developers to know the dependency graph. | Zero implementation cost. | Unscalable; error‑prone; poor onboarding experience. | Already causing pain; project growth demands automation. |
| **Two‑phase approach (chosen)** | Phase 1: Simple text file + Bash topological sort. Phase 2: Go‑based parallel scheduler. | Gradual adoption; minimal initial complexity; fits existing tooling. | Manual maintenance of dependency file; sequential builds in Phase 1. | Best trade‑off between immediate utility and future scalability. |

## Decision
We will implement a **two-phase build dependency system**:

### Phase 1: Simple dependency file + topological ordering (immediate)
- Create `SPECS/DEPENDENCIES` — a plain text file that lists each spec and its build dependencies (spec names only).
- Write `lib/depsolve.sh` — a Bash script that performs topological sort using Kahn’s algorithm or `tsort`.
- Extend `mql` CLI with a new subcommand: `mql rebuild <spec>` — finds all packages that depend on `<spec>` (directly or transitively) and builds them in dependency order.
- Builds remain sequential; parallelism is deferred to Phase 2.
- Dependency resolution is **static** (based on the `DEPENDENCIES` file) rather than parsing spec files dynamically.

**Format of `SPECS/DEPENDENCIES`:**
```
# spec: dep1, dep2, ...
# Lines starting with # are comments
# Empty lines ignored
# spec name matches .spec filename without extension
glibc:
gcc: glibc
binutils: glibc
python3: gcc, glibc
```

**Example workflow:**
```bash
# Update DEPENDENCIES after adding a new spec
$ echo "newpkg: glibc, gcc" >> SPECS/DEPENDENCIES

# Rebuild everything that depends on glibc after an update
$ mql rebuild glibc
→ depsolve.sh computes order: glibc → gcc → binutils → python3 → ...
→ Sequentially runs `mql build` for each package

# Show dependency tree
$ mql deps tree glibc
```

### Phase 2: Go‑based parallel build scheduler (future)
3–6 months from now, replace the Bash script with a Go program that:
- Parses `DEPENDENCIES` and optionally extracts `BuildRequires:` from spec files for validation.
- Builds a directed acyclic graph (DAG) of packages.
- Executes builds in parallel where dependencies allow, using a worker pool.
- Integrates with GitHub Actions runners for CI/CD (runs builds in the cloud).
- Provides a queue system, progress reporting, and build logs.

## Consequences

### Positive
1. **Predictable rebuilds**: Developers can safely update core libraries and automatically rebuild all affected packages.
2. **Onboarding**: New contributors can understand the package graph without reading every spec file.
3. **Foundation for CI/CD**: A dependency‑aware build system is prerequisite for automated testing and release pipelines.
4. **Minimal initial complexity**: Phase 1 uses simple text files and Bash, fitting the existing Maqui Linux tooling philosophy.
5. **No new runtime dependencies**: The `depsolve.sh` script uses only standard Unix utilities (`awk`, `tsort`, `comm`).

### Negative
1. **Manual maintenance**: Developers must keep `SPECS/DEPENDENCIES` up‑to‑date when adding or removing dependencies. (We can mitigate with a validation script that compares with spec file `BuildRequires:`.)
2. **Sequential builds in Phase 1**: Build times will not improve until Phase 2.
3. **Static analysis limitations**: The simple dependency file cannot capture conditional dependencies (e.g., `%ifarch i686`). We accept this limitation for now; conditional deps are rare in our tree.
4. **Risk of circular dependencies**: The topological sort will detect cycles and fail, forcing manual correction.

## Future Work
- **Phase 1.5**: Write a validation script that compares `DEPENDENCIES` entries with `BuildRequires:` lines in spec files and reports discrepancies.
- **Phase 2**: Design and implement the Go‑based parallel scheduler. Key features:
  - Worker pool with configurable concurrency.
  - Build queue with priority (e.g., core packages first).
  - Integration with `mql chroot` to isolate each build.
  - Web dashboard for monitoring (optional).
- **Phase 3**: Extend dependency tracking to runtime (`Requires:`) for generating minimal ISO images and rootfs tarballs.

## Notes
- The `SPECS/DEPENDENCIES` file **must be committed to Git**; it is part of the project’s build metadata.
- We will adopt the existing spec naming convention (filename without `.spec` extension).
- The dependency graph is **directed** and must remain **acyclic**; cycles indicate a packaging error.
- Phase 1 will be delivered as part of the `mql` CLI, not as a standalone tool.

## Implementation Details (Phase 1)

**File `SPECS/DEPENDENCIES` format:**
- One line per spec: `<spec-name>: <dependency-list>`
- Dependencies are comma‑separated spec names (no `.spec` suffix).
- Empty dependency list means the spec has no build dependencies.
- Comments start with `#` and are ignored.
- Lines can be split with `\` continuation (optional).

**Example:**
```
# Core system libraries
glibc:
gcc: glibc
binutils: glibc
python3: gcc, glibc
# End
```

**Algorithm in `lib/depsolve.sh`:**
```bash
# Pseudocode
read_deps() {
    # Parse DEPENDENCIES into associative arrays
    # Return forward and reverse adjacency lists
}

topological_sort() {
    # Kahn’s algorithm:
    # 1. Compute indegree for each node
    # 2. Queue nodes with indegree == 0
    # 3. While queue not empty:
    #    a. pop node, add to output
    #    b. decrement indegree of its dependents
    #    c. add new zero‑indegree nodes to queue
    # 4. If output size != node count → cycle detected
}

rebuild_order() {
    # Given a target spec, compute all reachable dependents
    # Return list sorted topologically
}
```

**Integration with `mql`:**
- New subcommand `mql rebuild <spec>` calls `lib/depsolve.sh` to get order, then iterates `mql build`.
- New subcommand `mql deps tree <spec>` shows the dependency tree.
- New subcommand `mql deps validate` checks for cycles and missing spec files.

## Compliance with Decision Framework
This ADR follows the project's decision‑framework checklist:

- **Maintenance**: The Phase 1 solution uses only Bash and standard Unix utilities, which are already present in the Maqui Linux chroot and on any POSIX‑compatible host. No external dependencies are introduced.
- **Dependencies**: No hidden toolchain requirements (Rust, Go, Python, systemd). Phase 2 will introduce a Go program, but that is optional and can be built after the Go toolchain is bootstrapped.
- **Compatibility with Maqui Linux**: The system works without systemd (OpenRC) and does not require any kernel or glibc features beyond what we already have.
- **Self‑hosting impact**: The dependency file and scripts reside on the build host, not inside the chroot/initramfs. They do not affect the bootstrap path.
- **Long‑term fit**: Phase 1 provides immediate relief while Phase 2 aligns with the project's goal of a fully self‑hosted, parallel build infrastructure. The design allows incremental replacement without breaking existing workflows.

## References
- [Kahn’s algorithm](https://en.wikipedia.org/wiki/Topological_sorting#Kahn's_algorithm)
- `tsort(1)` – Unix topological sort utility
- RPM spec `BuildRequires:` and `Requires:` tags
- Existing Maqui Linux build scripts: `scripts/build-spec.sh`, `lib/build.sh`

---
*Created: 2026‑04‑18*  
*Last updated: 2026‑04‑18*  
*Status: Proposed*
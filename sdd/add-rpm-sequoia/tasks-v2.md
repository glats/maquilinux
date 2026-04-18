# Tasks: Add rpm-sequoia Support (v2 - Unified Rust Spec)

> **Change**: `add-rpm-sequoia`  
> **Approach**: Single rust.spec with subpackages (rust, rustc, cargo, rust-std)  
> **Specs**: 3 (rust.spec, rpm-sequoia.spec, rpm.spec)  
> **Critical Path**: rust.spec → rpm-sequoia → rpm

## Phase 1: Spec Files (Foundation)

- [x] **TASK-001**: Create unified rust.spec with bootstrap stages
  - File: `SPECS/rust.spec`
  - Structure: stage0 (binary bootstrap) → stage1 (cross-compile) → stage2 (self-hosted)
  - Subpackages: rust (meta), rustc, cargo, rust-std
  - Blocked by: None
  - Est: 90 min
  - AC: `rpmbuild -bp SPECS/rust.spec` parses, 4 subpackages defined

- [x] **TASK-002**: Add rust subpackage definitions
  - File: `SPECS/rust.spec` (subpackage section)
  - Add: `%package rustc`, `%package cargo`, `%package rust-std`, `%package rust` (meta)
  - Blocked by: TASK-001
  - Est: 30 min
  - AC: `rpmspec -q --srpm SPECS/rust.spec` shows 4 binary packages

- [x] **TASK-003**: Configure rpm-sequoia.spec crypto backend
  - File: `SPECS/rpm-sequoia.spec`
  - Add: `--features crypto-nettle` for distro consistency
  - Blocked by: None
  - Est: 20 min
  - AC: spec explicitly sets nettle crypto backend

- [x] **TASK-004**: Update rpm.spec for Sequoia support
  - File: `SPECS/rpm.spec`
  - Add: `-DWITH_SEQUOIA=ON` and `BuildRequires: rpm-sequoia-devel`
  - Blocked by: None
  - Est: 20 min
  - AC: `grep -E "WITH_SEQUOIA|BuildRequires.*rpm-sequoia" SPECS/rpm.spec` matches

## Phase 2: Workflow Integration (Orchestration)

- [x] **TASK-005**: Create bootstrap-rust.yml with 3-job structure
  - File: `.github/workflows/bootstrap-rust.yml`
  - Jobs: rust (stage0→stage1→stage2) → rpm-sequoia → rpm
  - Blocked by: None
  - Est: 45 min
  - AC: `actionlint` validates, proper `needs:` chain

- [x] **TASK-006**: Add rust build cache configuration
  - File: `.github/workflows/bootstrap-rust.yml` (Job 1)
  - Cache: `~/.rustup` and `~/rust-bootstrap/` between stage builds
  - Blocked by: TASK-005
  - Est: 30 min
  - AC: stage2 reuses stage1 artifacts

- [x] **TASK-007**: Add disk space pre-flight check
  - File: `.github/workflows/bootstrap-rust.yml` (all jobs)
  - Check: `df -h $MQL_LFS` fails fast if < 20GB free
  - Blocked by: TASK-005
  - Est: 15 min
  - AC: Clear error message on insufficient disk

## Phase 3: Chroot Integration (Build Environment)

- [ ] **TASK-008**: Update enter-chroot-build.sh for rust toolchain
  - File: `scripts/enter-chroot-build.sh`
  - Add: Detect rust.spec multi-stage builds, inject bootstrap into chroot
  - Blocked by: None
  - Est: 40 min
  - AC: Script handles rust toolchain bootstrap transparently

- [ ] **TASK-009**: Add rust toolchain cleanup trap
  - File: `scripts/enter-chroot-build.sh`
  - Add: Remove temporary bootstrap artifacts after stage2 completes
  - Blocked by: TASK-008
  - Est: 20 min
  - AC: Cleanup runs on both success and failure

- [ ] **TASK-010**: Update mql.conf with rust bootstrap paths
  - File: `mql.conf`
  - Add: `MQL_RUST_STAGE0_URL`, `MQL_RUST_CACHE_DIR` variables
  - Blocked by: None
  - Est: 15 min
  - AC: Variables documented with defaults and env overrides

## Phase 4: Testing Gates (Quality Verification)

- [ ] **TASK-011**: Add rust stage verification in %check
  - File: `SPECS/rust.spec` (in `%check`)
  - Test: Stage2 `rustc --version --verbose` shows correct host triple
  - Blocked by: TASK-001
  - Est: 25 min
  - AC: Build fails if stage2 produces wrong architecture

- [ ] **TASK-012**: Add cargo functionality test
  - File: `SPECS/rust.spec` (in `%check` for cargo subpackage)
  - Test: `cargo new --bin testproj && cargo build` in temp dir
  - Blocked by: TASK-002
  - Est: 20 min
  - AC: Cargo can create and build a binary project

- [ ] **TASK-013**: Add rpm Sequoia linkage verification
  - File: `.github/workflows/bootstrap-rust.yml` (Job 3)
  - Test: `ldd $(which rpm) | grep -i sequoia`
  - Blocked by: TASK-004, TASK-005
  - Est: 15 min
  - AC: RPM binary links to librpm_sequoia.so

- [ ] **TASK-014**: Add RPM signature verification E2E test
  - File: `.github/workflows/bootstrap-rust.yml` (Job 3)
  - Test: Create test RPM, sign with test key, verify with `rpm -K`
  - Blocked by: TASK-013
  - Est: 35 min
  - AC: Output shows "digests signatures OK"

## Phase 5: Documentation

- [ ] **TASK-015**: Document unified rust spec in DEVELOPMENT.md
  - File: `docs/DEVELOPMENT.md`
  - Add: Section on "Rust Bootstrap (3-stage with subpackages)"
  - Blocked by: All spec tasks
  - Est: 30 min
  - AC: Explains stage0→stage1→stage2 flow and subpackage structure

- [ ] **TASK-016**: Update AGENTS.md with rust bootstrap notes
  - File: `AGENTS.md`
  - Add: Cache paths, chroot integration notes, cargo test procedure
  - Blocked by: TASK-008
  - Est: 15 min
  - AC: Agent reference for rust toolchain handling

---

## Summary

| Phase | Tasks | Est. Total | Focus |
|-------|-------|------------|-------|
| 1: Spec Files | 4 | 2h 40m | Unified rust.spec + 2 dependent specs |
| 2: Workflow | 3 | 1h 30m | 3-job GitHub Actions |
| 3: Chroot | 3 | 1h 15m | Bootstrap integration |
| 4: Testing | 4 | 1h 35m | Stage/subpackage verification |
| 5: Documentation | 2 | 45m | Updated docs for unified approach |
| **Total** | **16** | **~8h** | |

### Critical Path

```
TASK-001 → TASK-002 → TASK-005 → TASK-008 → TASK-011 → TASK-012 → TASK-013 → TASK-014
     │         │           │          │         │         │         │         │
   rust    cargo pkg   workflow   chroot    stage    cargo   sequoia    e2e
   spec    defined      setup      support   verify   verify  linkage   test
```

**Longest chain**: 8 tasks (rust foundation → workflow → chroot → verification)  
**Parallelizable**: Spec fixes (TASK-003, TASK-004 can run with TASK-001/002)

### Key Changes from v1 (5-spec approach)

| Aspect | v1 (5 specs) | v2 (3 specs) |
|--------|--------------|--------------|
| Spec files | rust-stage0, rust, cargo, rpm-sequoia, rpm | rust, rpm-sequoia, rpm |
| Rust structure | Separate stage0/cargo specs | Unified spec with subpackages |
| Workflow jobs | 5 sequential jobs | 3 sequential jobs |
| Bootstrap cache | 2 caches (stage0, stage1) | 1 cache (unified rust) |
| Total tasks | 20 | 16 |
| Critical path | 9 tasks | 8 tasks |

### Deliverables

- [x] `SPECS/rust.spec` (new unified spec with 3-stage bootstrap)
- [x] `SPECS/rpm-sequoia.spec` (updated)
- [x] `SPECS/rpm.spec` (updated with Sequoia flags)
- [x] `.github/workflows/bootstrap-rust.yml` (3-job workflow)
- [ ] `scripts/enter-chroot-build.sh` (rust-aware)
- [ ] `mql.conf` (rust variables)
- [ ] `docs/DEVELOPMENT.md` (updated)
- [ ] `AGENTS.md` (updated)

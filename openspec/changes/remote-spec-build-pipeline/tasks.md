# Tasks: Remote Spec Build Pipeline

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~530 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | Phase 1 (PR #1) -> Phase 2 (PR #2) -> Phase 3 (PR #3) |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Phase 1: Order and Document | PR 1 -> main | Bug fixes + docs + schema. No CI changes. |
| 2 | Phase 2: CI Remote | PR 2 -> main | New CI workflow using build-chain.sh. Depends on Phase 1 --json output. |
| 3 | Phase 3: External Contributors | PR 3 -> main | Design outline only. Independent. |

---

## Phase 1: Order and Document

- [x] **1.1** Fix `--both` in `scripts/build-spec.sh` -- remove broken `exec` pattern, add actual i686 loop after x86_64. [S] [Dep: none] [Verify: `./build-spec.sh <pkg> --both` produces RPMS/ for both arches]
- [x] **1.2** Add `--json` flag + structured state file output to `scripts/build-chain.sh` -- JSON summary with per-spec status, duration, log path. Add `--continue-on-failure` flag. [M] [Dep: none] [Verify: `./build-chain.sh <specs> --json` produces valid JSON on stdout]
- [x] **1.3** Create `maqui-build.yaml` at repo root with optional `defaults`/`specs`/`jobs` schema. Document schema in file comments. [S] [Dep: none] [Verify: file exists with valid YAML structure per design.md]
- [x] **1.4** Create `agent_docs/acceptance-tests.md` -- document verification flow: rpm -q, rpm -V, binary --version, ldd linkage. Include JSON result schema. [S] [Dep: none] [Verify: file documents all 5 check types + failure blocks publish]
- [x] **1.5** Create `agent_docs/backup-flow.md` -- document backup lifecycle (pre-build, post-success, post-failure restore), push-vs-read boundary table, museum storage model. [S] [Dep: none] [Verify: file includes boundary table + restore command]
- [x] **1.6** Update `agent_docs/build-workflow.md` -- expand from 6 to 7 steps, add acceptance test step (step 6), add `--json` output section, cross-reference acceptance-tests.md and backup-flow.md. Keep under 100 lines. [S] [Dep: 1.4, 1.5] [Verify: pipeline has 7 steps, cross-refs present]
- [x] **1.7** Create `docs/agents/standalone-developer.md` -- document Path A (Nix shell: `nix develop`) and Path B (standalone: apt/dnf/pacman). Include rootfs download, MQL_ROOTFS setup, first chroot entry. [S] [Dep: none] [Verify: file documents both setup paths + rootfs extraction]
- [x] **1.8** Update `AGENTS.md` -- add `agent_docs/acceptance-tests.md` (stable) and `agent_docs/backup-flow.md` (mostly-stable) to Agent Documentation Index. Bump `agent-context-version` to `2`. [S] [Dep: 1.4, 1.5] [Verify: index has 2 new entries with stability labels]

## Phase 2: CI Remote

- [ ] **2.1** Create `scripts/acceptance-test.sh` -- post-build verification script with JSON output. Checks: rpm -q (must pass), rpm -V (must pass), binary --version (warn on fail), ldd linkage (warn on fail), multiarch lib path check. [M] [Dep: 1.4] [Verify: `./acceptance-test.sh <spec> --json` outputs valid JSON per design schema]
- [ ] **2.2** Create `.github/workflows/build-rpms-v2.yml` -- new CI workflow delegating to build-chain.sh --json, acceptance-test.sh, artifact upload (logs + RPMs), per-spec PR comment via actions/github-script, restore-on-failure step. [L] [Dep: 1.2, 2.1] [Verify: workflow handles push, PR (validate), workflow_dispatch; artifacts uploaded; PR gets per-spec comment]
- [ ] **2.3** Ensure `scripts/build-chain.sh` has `--state-file .ci-build-state` and `--json` consumable by CI for per-spec status checks. [S] [Dep: 1.2] [Verify: both flags exist and work with CI context]

## Phase 3: External Contributors

- [ ] **3.1** Create `agent_docs/external-contributors.md` -- design outline only. Document per-PR overlay isolation approach, `allowed_pr_authors` gate, throwaway overlay lifecycle, cleanup on PR close. No implementation. [S] [Dep: none] [Verify: file exists with isolation design outline + references to Phase 2 CI pattern]

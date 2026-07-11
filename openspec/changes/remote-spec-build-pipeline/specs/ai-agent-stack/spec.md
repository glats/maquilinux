# Delta for AI Agent Context Stack

## MODIFIED Requirements

### R.4: agent_docs/build-workflow.md

MUST document a 7-step pipeline: spec creation, source fetching, overlay mount, build, install, acceptance test verification, repo update. Each step: exact `mql` command, flags, and verification. Steps 1-5 unchanged from current. Step 6 (new): MUST include acceptance test verification commands: `rpm -q <pkg>`, `rpm -V <pkg>`, `<binary> --version`, `ldd` on shared libraries. MUST reference `agent_docs/acceptance-tests.md` for full test specification. Max 100 lines (expanded from 80). MUST NOT contain architecture theory or troubleshooting (defer to `agent_docs/troubleshooting.md`). Source: `scripts/build-spec.sh`, `scripts/install-spec.sh`, `build-acceptance-tests` spec. Evolvability: mostly-stable. Verify: all 7 steps documented; acceptance test commands present; cross-reference to `acceptance-tests.md` present.

(Previously: 6-step pipeline, max 80 lines, no acceptance test step, no reference to acceptance-tests.md. Build was step 4, install was step 5, repo update was step 6.)

#### Scenario: Agent follows full pipeline with acceptance tests

- GIVEN an agent requested to build a package
- WHEN the agent reads `build-workflow.md`
- THEN the agent executes all 7 steps including acceptance test verification
- AND the agent knows to run `rpm -q`, `rpm -V`, binary `--version`, and `ldd` checks

## ADDED Requirements

### Agent Documentation Index: Acceptance Tests and Backup Flow

The agent documentation index in `AGENTS.md` MUST include new entries for `agent_docs/acceptance-tests.md` (per-package verification flow after build: rpm -q, rpm -V, binary execution, ldd linkage) and `agent_docs/backup-flow.md` (backup lifecycle: pre-build create, post-build success create, post-build failure restore). Stability classification: `acceptance-tests.md` (stable), `backup-flow.md` (mostly-stable).

#### Scenario: New agent_docs files appear in AGENTS.md index

- GIVEN a fresh checkout of maquilinux
- WHEN an agent reads `AGENTS.md`
- THEN the agent_docs/ index includes `acceptance-tests.md` and `backup-flow.md`
- AND each entry has a one-line description and stability classification

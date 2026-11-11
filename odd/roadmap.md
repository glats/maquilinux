# Maqui Linux: distribution roadmap

Objective: maintained independent physical/VM/container distribution. Initiative: `maqui-distribution`.
Status: legacy ownership mapped; isolated split-transition/preservation scope awaits confirmation, no ISO (CP32). Shared-system/delivery boundaries preserved.
Branch: `feat/distro-quality-stack` | Source baseline: `1e7ba6716a85ea240cd25f4a2e4b392327c3ef8e` | Mirror: project `maquilinux`, topic `odd/maqui-distribution/roadmap`.

## Specs

### Executive brief

Maintained, installable physical/VM distribution, container base and desktop path on RPM/DNF5/OpenRC. Console demonstration is only the first delivery.

```text
R1: trusted console VM -> R2: persistent VM/bare-metal installation -> R4: desktop
                      -> R3: official container base
```

R3 needs a trusted base, not all R2 hardware work. Security, packagers, docs and maintenance apply throughout. Delivery table owns exit criteria/progress.

| Read for | Authoritative location |
|---|---|
| Product scope, capability coverage, delivery routes and current checkpoint | This roadmap; epics are coverage, not separate work queues |
| R1 decisions, dependencies, acceptance, tasks and evidence | [cli-mvp](tasks/cli-mvp.md); start at D1, then refine the next dependent task |
| Original intent and current documented identity | [Distro.md](../Distro.md) and [DISTRO-IDENTITY.md](../docs/DISTRO-IDENTITY.md); historical/context inputs, not additional task ledgers |

Qualify the first slice. Refine only upcoming tasks: decisions, outcomes, surfaces, resources and checks; no launch-ready parallel writers yet. Future children remain named, unexpanded until selected.

### Resume here

Current checkpoint: **CP32** (Log). Reconcile feature/mirrors/execution; no duplicate ledgers/jobs/exploration.

### User intent and scope

- **S1 — The distribution is the product.** "en verdad maqui quiere ser una distro al nivel de gtodas las otras. esa es la verdad. y se tiene que instalar en bare metal y vm donde sea docker. etc. quiere verni a ser una distro. para eso me tienes que ayudar a definir lo que se necesita y deividrlo en epicas quizas no se (por decirlo de alguna manera) para poder llevar a acabo esto. hay experiencia previa de otras distros y esta es la idea aca. todo lo demas esta bien pero creo que el enfoque debe ser eso l marco y vamos viendo los hijos y nombrandolos, ok?" The terminal VM MVP is an early delivery, not Maqui's final scope. Define a parent initiative, capability epics and named child features before expanding implementation tasks.
- **S2 — Original vision as evidence.** "dejo aca Distro.md el documento incial original por si aaporta". Read [Distro.md](../Distro.md) as the historical founding proposal; preserve it unchanged. Trace useful goals forward, but do not silently reinstate historical choices or unverified technical claims.
- **S3 — Carry forward the accepted working principles.** The earlier user requirements remain recorded verbatim in [cli-mvp](tasks/cli-mvp.md), S2/S4/S5: signed-package E2E, a usable packager path, controlled rollout, infrastructure portability, agent-facing planning and identical Engram structure. This parent changes their placement, not their validity.
- **S4 — Durable checkpoints.** "quiero primero guradar todo y dejar todo listo para los pmactcion de reincio o nueva sesiones"; clarified as "la idea es tener checkpooints o algoasi apra ver donde estamos parados y no partir de nuevo siempre". Keep a named current checkpoint with completed evidence, active work, unresolved decisions and exact next step; preserve it in this document and its existing full mirror. A checkpoint does not authorize implementation or substitute for Git backup.

Judge working capabilities/maintenance, not image/tool/agent counts. Releases need supported targets, usable install/execution, trust, upgrades, bounded recovery, docs and maintainers; not identical staffing or universal desktop/architecture/hardware support.

Baseline: RPM/DNF5/OpenRC/glibc/GCC, x86_64+i686; [identity](../docs/DISTRO-IDENTITY.md) specifies YY.MM point releases. Preserve unless explicitly changed. Documentation is neither runtime proof nor upgrade authority.

### Delivery-led navigation and capability coverage

```text
maqui-distribution                  vision and capability map (EP01 ... EP08)
  selected delivery (R1 ... R4)     supported outcome and acceptance boundary
    selected feature (F01 ... F10)  one authoritative feature document
      next decision/task           acceptance checks and retained evidence
```

Parent owns direction/epics/feature IDs/dependencies. Each `odd/tasks/<feature>.md` owns requirements/status/evidence/Log. Milestones are outcomes, not databases; cross-epic features have one owner and supporting references, never copied tasks.

Epics map coverage, not queues. Select delivery/feature outcomes; child owns acceptance/tasks/evidence, no separate matrix. Task completion and delivery acceptance are distinct, evidence-linked claims.

Entry: R1/F01/`cli-mvp/T2`, reusing T1/E9/L23. D1 owns initial platform, F06 generalizes later. Navigation grants no operational authority.

Only F01 is expanded; other names reserve scope. No empty children/epic ledgers/giant backlog. Hierarchy acceptance does not authorize implementation.

### Supported-target contracts

All three target classes are in the product direction. Their exact support matrices remain to be defined; no runtime support is certified by this roadmap.

| Target | Expected product capability | Evidence required before a support claim | Boundary |
|---|---|---|---|
| Bare metal | Install Maqui persistently on selected physical hardware; boot, use the system, update and recover within declared limits | Installation safety checks; boot without installation media; reboot persistence; storage/network/firmware tests on named profiles; relevant package and upgrade checks | Real-disk operations require explicit device selection and authorization. VM success is not physical-hardware certification |
| Virtual machines | Persistent installation and/or official prepared images for declared hypervisor/firmware combinations | Disk installation or image deployment, independent boot, reboot persistence, guest network/storage, signed packages, updates and recovery | A live ISO smoke test alone is not a persistent installation. Choose image formats and firmware scope per feature |
| Containers | A Maqui userland/base image usable with a declared Docker/OCI-compatible runtime and host combination | Image provenance, clean pull/run, architecture compatibility, package operations, application execution and rebuild/update lifecycle | Linux containers use the host kernel; they do not boot Maqui's kernel or prove the physical/VM installer. No universal runtime/host-kernel claim |

Rootfs archives, source packages and installation media may serve developers and multiple target classes, but are not interchangeable proof. A container base does not need to emulate a full OpenRC boot; its process contract must be chosen deliberately. New architectures, hypervisors, Secure Boot support or hardware families require explicit scope and evidence, not the word "everywhere".

### Capability epics

All epic definitions are proposed. A first feature delivers a narrow supported portion; an epic is not globally "done" because one demonstration passes.

| ID / name | Expected capability | Reuse and current evidence | Missing definition or proof | Completion evidence for a declared release scope |
|---|---|---|---|---|
| EP01 / System foundation and platform support | A coherent bootable base: toolchain, kernel, libc, init/services, filesystem policy, architecture and firmware contract | Current identity; existing RPM specs, OpenRC and filesystem lint from the previous feature | Current base/ABI compatibility, supported hardware/firmware matrix and repeatable clean base build are not certified here | Versioned package set and support matrix; build/boot/service/multiarch tests for the selected scope |
| EP02 / Packaging and packager workflow | Maintainable recipes, declared dependencies, package policies, clean builds and safe contributor participation | `SPECS/`, mql build, dependency guidance and lint exist; first-loop mapping in F01 | External contributor isolation, ownership/review policy, source/license provenance and repeatability need evidence | A new packager builds/checks/submits without release secrets; traceable artifacts; policy regressions caught |
| EP03 / Trust, updates and security maintenance | Trust bootstrap, signed distribution artifacts/packages, safe update channels, key lifecycle and vulnerability response | Client signature configuration and signing code exist; F01 records warning-only failure handling | End-to-end enforcement, supported upgrade paths, key/revocation expectations, support windows and response ownership | Negative trust tests fail safely; supported upgrades and scoped recovery pass; publication blocks on failed checks; documented security responsibilities |
| EP04 / Installation, boot and recovery | A persistent installed system on VM and selected physical machines, with safe setup and recovery procedures | Original terminal/graphical installer goals; existing ISO path; current installer docs are not installation proof | Installer design/tool choice, disk-safety contract, firmware/storage coverage and actual persistent installation | Authorized install/reboot/update/recovery drills with retained evidence; rejection preserves non-target disks |
| EP05 / Images and distribution channels | Versioned installation/live media, VM images, developer rootfs and container artifacts built from a coherent package set | Existing ISO/rootfs generation and publication paths; original container ambition | Artifact-specific manifests/trust, OCI pipeline, tested VM image formats and current public download path | Each advertised artifact can be obtained, authenticated and used for its declared purpose; source and package versions trace back to the release |
| EP06 / Desktop and daily use | A supported graphical session and practical desktop experience on the declared targets | Original Cinnamon/light/base proposals; historical desktop tasks remain pending | Desktop/session stack selection; graphics, input, audio, networking, permissions and application integration | Install, login, session lifecycle, essential apps and relevant device tests on selected profiles |
| EP07 / Quality and release engineering | Repeatable qualification of supported targets and a controlled candidate-to-stable release process | Existing Bats/lint checks and CI; F01 distinguishes chroot checks from VM proof | Complete E2E, negative tests, artifact/channel consistency and release acceptance matrix | A release candidate passes its declared matrix; failed checks stop promotion; retained evidence identifies exactly what was released |
| EP08 / Project stewardship and operations | Sustainable maintenance: contributor/user docs, ownership, support and issue channels, release notes, licensing and recoverable portable hosting | Original community goals, existing docs, public-domain and portability work | Ownership/maintenance capacity, accurate onboarding, lifecycle policy and operational recovery proof | A contributor and user can follow the documented paths; supported releases have owners and limits; authorized restore/move rehearsals validate runbooks |

Security, documentation and release quality apply to every delivery; EP03/EP07/EP08 are not permission to postpone them until the end. Reuse existing infrastructure while isolating configuration from machine identity. A new server fleet, custom package manager or agent platform is not an epic prerequisite.

### Original vision: disposition, not automatic adoption

`Distro.md:102` explicitly calls the text a declaration of intentions. Use it to avoid losing product ambition while separating desired outcomes from old implementation proposals.

| Original reference | Carry forward | Revalidate or leave undecided |
|---|---|---|
| `Distro.md:112-122` | Managed release points, development/testing flow, security/bugfix maintenance -> EP03/EP07 | Two releases per year, two-year LTS and exact branch policy are not current commitments. Point releases and YY.MM do not by themselves settle support duration |
| `Distro.md:126-130,234-242` | Installable desktop and base variants, including a terminal path -> EP04/EP05/EP06 | Three ISO flavors, Cinnamon/LXDE/MATE and Calamares are historical proposals, not automatically selected tools or release requirements |
| `Distro.md:134-160` | OpenRC and a coherent service/session/boot environment -> EP01/EP06 | Old maintenance claims about alternative session/initramfs tools must be researched again; do not inherit an obsolete two-option choice |
| `Distro.md:170-188` | Package composition appropriate to desktop, development and container use -> EP02/EP05 | Aggressive splitting and automatic dependency/removal semantics require independent tests and a maintainer-cost decision; no package-manager rewrite is authorized |
| `Distro.md:194-202` | Explicit firmware and licensing policy -> EP01/EP02/EP08 | Redistribution rights, optional non-free content and maintained source obligations need current review; do not treat the historical prose as a blanket permission |
| `Distro.md:206-226` | Repository ownership, x86_64 focus and 32-bit x86 compatibility -> EP01/EP02/EP03 | Official/community repository boundaries and other architectures need explicit support decisions. x86 multilib was already in the original vision; current i686 multiarch is not proof of a new standalone 32-bit edition |
| `Distro.md:228-242` | Identifiable releases and persistent installation -> EP04/EP05/EP07 | Historical major/minor ISO numbering differs from current YY.MM identity; resolve naming deliberately without changing existing consumers |
| `Distro.md:244-343` | Maintainable tooling, collaboration and community conduct -> EP02/EP08 | Historical hosting/language choices and financing statements do not establish current capacity or require migration |

Current repository identity and actual code must still be reconciled before implementation. Preserve [Distro.md](../Distro.md), [DISTRO-IDENTITY.md](../docs/DISTRO-IDENTITY.md), the [previous ODD feature](tasks/distro-quality-stack.md) and historical OpenSpec artifacts. No old task is converted or marked complete by this map.

### Prior art and its limits

- [Fedora Cloud deliverables](https://fedoraproject.org/cloud/download) illustrate separately packaged VM/cloud images and verification material within a distribution that also offers installation and container variants. This supports artifact-specific contracts, not importing Fedora's infrastructure or every image format.
- [Alpine downloads](https://alpinelinux.org/downloads/) distinguish Standard/Extended media, Virtual media and a mini root filesystem for containers/chroots. [Its installation guide](https://docs.alpinelinux.org/user-handbook/0.1a/Installing/setup_alpine.html) illustrates a terminal-driven installation path. A GUI installer is not the only possible first persistent installation path; no Alpine component migration is implied.
- [Docker's overview](https://docs.docker.com/get-started/docker-overview/) describes images/containers and isolation; the [container/VM comparison](https://aws.amazon.com/compare/the-difference-between-docker-vm/) distinguishes shared-host-kernel containers from VMs with their own guest kernels. Choose separate boot and container qualification checks.
- [Chimera history](https://chimera-linux.org/docs/history), already checked in prior research, shows incremental build tooling, bootability and later release artifacts. It does not prove a universal initial console-only ISO rule. Reuse the bounded evidence and caveats in Engram 4452 rather than rerun that research on every session.

Research identifies useful capability boundaries, not an approved Maqui architecture. No qcow2 pipeline, installer, release cadence, desktop or signing technology was selected by these references. Package inventory/integrity checks alone are not proof of signature trust or a persistent OS installation.

## Tasks

### Named child feature catalog

This parent section is an index of children, not a duplicate implementation task ledger. Except F01, these are named candidates with no child file or task decomposition yet. Feature proposals are neither approved implementation nor claims that the corresponding code is absent. One outcome may reuse existing work; map its evidence before creating tasks.

| ID / stable feature identity | Owning epic; supporting epics | Bounded outcome to refine | Dependencies / scope boundary | Record |
|---|---|---|---|---|
| F01 / `cli-mvp` | EP07; EP01/EP02/EP03/EP05 | First trusted console VM loop, one representative package, initial contributor path and controlled promotion exercise | Select a minimal platform contract first; does not qualify persistent bare-metal installation or the complete distro | [Existing draft and authoritative tasks](tasks/cli-mvp.md); mirror `odd/cli-mvp/tasks` |
| F02 / `installable-base` | EP04; EP01/EP03/EP07 | Persistent base installation, reboot and recovery in VM, then a selected physical profile | Reuse F01 proof; destructive disk operations need explicit authorization. Installer/tool and firmware decisions remain open | Named candidate; not expanded |
| F03 / `oci-base-image` | EP05; EP01/EP03/EP07 | Versioned Maqui container base with authenticated provenance, package operations and application execution | Reuse trusted base/package outputs; own runtime/host contract. Does not depend on completing the desktop or all physical installation coverage | Named candidate; not expanded |
| F04 / `packager-workflow` | EP02; EP03/EP08 | Extend the F01 demonstration to a maintained contributor workflow with clean builds, isolation, review and package ownership | Reuse F01/T5/T7 results when valid; do not rebuild their onboarding as a competing system | Named candidate; not expanded |
| F05 / `trusted-release-lifecycle` | EP03; EP07/EP08 | Supported upgrade channels, signing/key lifecycle, bounded recovery and security-maintenance policy | Extend F01's package-level proof to the supported release set; no promise of arbitrary whole-system rollback | Named candidate; not expanded |
| F06 / `platform-support-contract` | EP01; EP04/EP07 | Generalize supported architectures, firmware, VM and physical profiles, base services and support tiers | Reuse the initial R1 contract recorded only in cli-mvp/D1; expand coverage with evidence without creating a second authority for that decision. Preserve existing multiarch intent | Named candidate; expand when broader coverage is selected |
| F07 / `desktop-session` | EP06; EP01/EP02/EP04 | One supported desktop/session and everyday-use path before considering multiple editions | Select stack based on current evidence and installed-system support; old desktop proposals are inputs, not selections | Named candidate; not expanded |
| F08 / `release-images` | EP05; EP03/EP07/EP08 | Coherent versioned image/rootfs composition, public downloads and artifact-specific verification | Reuse builders and F01/F02/F03 outputs; prepared VM formats are selected only if the delivery contract needs them | Named candidate; not expanded |
| F09 / `project-maintenance` | EP08; EP02/EP03/EP07 | Maintainer/contributor/user guidance, support channels, licensing/source obligations and portable operational runbooks | Basic docs and ownership begin with the first delivery; staffing and support promises must match actual capacity | Named candidate; not expanded |
| F10 / `release-qualification` | EP07; all declared release capabilities | Repeatable release acceptance matrix and retained candidate/promotion evidence | Reuse feature tests, not a second harness per epic. Qualify only advertised targets/editions; do not wait for every future feature | Named candidate; not expanded |

F01 intentionally crosses capability areas as a small end-to-end delivery. The later children generalize only proven needs beyond that demonstration. If refinement reveals overlap, retain one implementation owner and link the existing task/evidence instead of cloning it. Do not make a new child merely to rename work.

### Progressive delivery milestones

These are proposed product increments, not dates or completed phases. Trust, documentation, update safety and evidence are required for the capabilities each increment advertises.

| ID | Product increment | Main child references | Observable exit boundary |
|---|---|---|---|
| R1 | Trusted console VM demonstration | F01 owns the initial contract (D1), tasks and detailed acceptance. F04/F05/F08/F09/F10 reference its evidence rather than opening competing R1 tasks | Another tester can obtain/verify the chosen artifact, boot it and use the signed-package loop. This is not yet general installation support |
| R2 | Installable base distribution | F02, selected F06 profiles; release/support work from F04/F05/F08/F09/F10 | Persistent installation and reboot without installation media in VM and on declared physical hardware; documented upgrades and scoped recovery |
| R3 | Official container base | F03 plus corresponding F05/F08/F10 contracts | Obtain and run a Maqui container image on the selected runtime, verify provenance and exercise its package/application lifecycle. Can develop independently of R2 after the trusted base exists |
| R4 | Desktop distribution on supported profiles | F07, installed-base and hardware proof from R2; relevant release/support work | Install and use the selected graphical session and essential applications on declared targets. Multiple editions are a later explicit choice |

After each increment, evaluate what worked, update the same evidence and refine only the next selected child. A distribution remains a maintenance commitment after a release; R4 is not the end of updates, security response or platform qualification.

### Agent and Engram continuation contract

- Start from this parent and the selected child, not the newest global memory. Parent mirror: `odd/maqui-distribution/roadmap`; child mirrors: `odd/<feature>/tasks`, all under the discovered project `maquilinux`. Each mirror stores its locator and the entire current document, with identical headings and IDs, not an executive summary.
- Mirror capacity: when raw UTF-8 exceeds the provider limit, the same observation/topic may store the entire document as `gzip+base64` with `Locator`, `Encoding`, `Decoded-Bytes` and decoded `SHA256` headers, then `Payload:` and one Base64 line. Decode using Python `gzip.decompress(base64.b64decode(payload, validate=True))`; verify byte count and SHA-256 before reading/reconciling the full decoded document. This is lossless storage, not a summary or another ledger. Preserve observation history; never truncate quotes, requirements or Log. Readback must match the saved encoded envelope and decoded source hash. Legacy plain `Locator` mirrors remain readable; never assume encoded bodies are literal Markdown documents.
- Canonical mirror writes are parent-owned. Delegates may save discoveries only under distinct non-authoritative finding topics, never parent/child mirror IDs or topics. If a mirror is replaced by a summary, preserve that observation separately, reconcile the previously verified local file/hash, restore the complete mirror and verify exact readback before claiming recovery.
- Parent IDs are `maqui-distribution/EP01`, `maqui-distribution/F01`, `maqui-distribution/R1`. Child task/evidence IDs remain, for example, `cli-mvp/T4` and `cli-mvp/E1`. Do not renumber existing records or infer that old `distro-quality-stack/T4` is the same task.
- This parent owns catalog/dependency changes only; task progress and proof are authoritative in the child. Parent milestones reference that proof without copying status tables. Update only the documents actually affected and their corresponding existing mirror topics; no parallel summary becomes another task authority.
- On resume, discover project, read context, search exact parent/child topics, retrieve full observations and read the real files. Reconcile branch/diff and relevant evidence. Preserve conflicting versions; never silently choose by timestamp. Reuse unchanged evidence and record why any retest is needed.
- Before expanding a child, confirm its outcome, exclusions, scope decisions and existing implementation/evidence. Then create or update that one feature's Specs/Tasks/Log, link it here, and break it into bounded tasks with acceptance checks. Do not create all candidate files in advance.
- This section owns shared continuation rules. Children link here and retain only their own locator, IDs, task/evidence semantics and genuine exceptions; do not maintain duplicate operating instructions in each child.
- At a meaningful decision, completed task, blocker or session handoff, append the next CP number under Log and update the current-checkpoint pointer. Do not create a new checkpoint for unchanged state or every tool call. Record the completed outcome and evidence references, selected delivery/feature, pending decision/task, authorization boundary, branch/revision and uncommitted state. Preserve older checkpoints as history; child task records remain authoritative.
- Save the full parent to the same mirror topic after checkpoint changes, and save a child only when it changed. Read back both relevant mirrors before claiming a synchronized handoff. If synchronization fails, report it and mark it pending; never claim recovery is complete. On resume, reconcile changes since the checkpoint and rerun only invalidated or missing proof, not the whole exploration by default.
- The user authorized autonomous routine progress after CP02; see child L10 for the exact instruction. Reversible implementation and isolated checks within the agreed feature may proceed without repeated approval. Stop for consequential product/stack decisions, destructive operations, credentials, production or publication. Do not infer staging, commit, push, shared-rootfs mutation, deployment or service-restart permission. Preserve historical documents and repository policy.
- When implementation is later authorized, preserve repository policy, deterministic test-first checks where applicable, bounded delegation and independent verification for security/data/delivery risk. A passing isolated VM test does not authorize physical installation or release. No new workflow tooling is required to use this map.

### Asynchronous execution for future sessions

Use native OpenCode V2 background execution for authorized long commands, keeping the parent conversation available. `shell(background: true)` runs the process asynchronously; `subagent(background: true)` delegates an independent unit when delegation is otherwise warranted. Both notify on completion. A reusable slash command can use `subagent: true`, but creating one is optional, not a prerequisite or an action performed by this decision. No plugin is required. References: [V2 tools](https://opencode.ai/v2/docs/tools/) and [commands](https://opencode.ai/v2/docs/commands/); research observation 4493.

- Set explicit resource and timeout bounds; background tools otherwise have no default timeout. Give one cost forecast, then retain the exact command, input identity, working root, tool/task/session ID, log/artifact locators, start time and final exit/result in the existing child evidence. Do not create another status ledger. Completion notification is not acceptance: verify outputs independently when required.
- Keep one owner per mutable build environment. Parallel agents may handle independent files/resources; never race on the same chroot, signing state or publication target. More agents do not accelerate one compression process. Measure CPU/IO before tuning resources.
- Resume from the recorded execution identity. Reconcile its actual state and retained output before launching anything; never duplicate a possibly running build after compaction or a new session. Consume native completion notifications rather than polling. Missing or ambiguous state is pending, not success or permission to rerun.
- Do not promise survival across service restart or host reboot. Native documentation establishes asynchronous notifications, not crash durability. Temporary artifact paths may disappear. A durable external executor is a separate design decision if required, not an automatically installed service.
- Background execution never expands authorization or overrides a user pause. Keep secrets out of logs/memory. No OpenCode configuration, command file, plugin, runner or service was changed to record this convention.

### Next planning step

Continue T2 within L23: separately assembled console-only disposable derivative, independent scope inspection, then bounded offline guest commands/shutdown. Reuse T1/E9 and reconcile background work before launching anything. Networking remains separately scoped; T9 owns runner recovery. Epics remain coverage, not parallel queues.

## Log

- **L1 — 2026-10-23, product framing correction (verbatim):** "en verdad maqui quiere ser una distro al nivel de gtodas las otras. esa es la verdad. y se tiene que instalar en bare metal y vm donde sea docker. etc. quiere verni a ser una distro. para eso me tienes que ayudar a definir lo que se necesita y deividrlo en epicas quizas no se (por decirlo de alguna manera) para poder llevar a acabo esto. hay experiencia previa de otras distros y esta es la idea aca. todo lo demas esta bien pero creo que el enfoque debe ser eso l marco y vamos viendo los hijos y nombrandolos, ok?"
- **L2 — 2026-10-23, original vision supplied (verbatim):** "dejo aca Distro.md el documento incial original por si aaporta". Source supplied as historical context, not automatic approval of every earlier proposal.
- **L3 — 2026-10-23, planning evidence and route:** Parent authors planning documents inline. Read-only explorer `ses_e962bf94bffemZe8nMuT0MbBlv` mapped original intentions and reference distribution artifacts because this cross-domain mapping exceeded the inline evidence budget. Parent spot-checked `Distro.md:100-244`; current identity was read as documentary context. Research does not authorize qcow2, Calamares, a particular desktop, or a release cadence; package inventory checks are not treated as full installation/trust proof.
- **L4 — 2026-10-23, preservation baseline:** Source revision `1e7ba6716a85ea240cd25f4a2e4b392327c3ef8e`; Distro.md SHA-256 `b5ecbd37ae0960eee2427f5397aa9fdacb8f9cd528b52d1a9c05df3f1054e762`; current identity SHA-256 `8a31471bd2384bbb82f29ac45380848d6ef2558c34c07a64effc22b71be95ed7`; previous ODD SHA-256 `ab5753a2f76971b58f0294a22a539ef06dd3b99383fe3658be8f5bcf3d1de6ce`. All remain historical/current inputs, unchanged by this plan. F01's prior file and full mirror 4456 were reconciled before updating its parent relationship.
- **L5 — 2026-10-23, scope status:** Created a distribution-wide draft with eight epics, ten named child features and four proposed delivery increments. Only F01 has a feature document; no implementation task or runtime milestone was completed. Structural document checks and full mirror readback are separate from product verification.
- **L6 — 2026-10-23, approved simplification (verbatim):** "si adelante". In response to the proposal to organize execution by deliveries while retaining epics as capability coverage, the user authorized this documentation simplification. Preserve all IDs and history. R1/F01/D1 now owns the initial platform decision; F06 generalizes it later. Shared continuation rules stay here. Child T3 owns validated signed candidates, while T6 owns promotion and recovery. No implementation or platform choice was authorized. Advisory references: Engram 4461 and 4464.
- **E1 — 2026-10-23, planning checks:** Inline Python check exited 0 for Specs/Tasks/Log order, 3 parent specs, 8 epic IDs, 10 feature IDs, 4 delivery increments, local Markdown links and reciprocal F01 ownership. Original vision/identity/previous-ODD hashes match L4; `git diff --exit-code HEAD` exited 0. Both planning documents passed `git diff --no-index --check` with no diagnostics (exit 1 denotes new-file content). Only the parent and existing untracked child planning documents are pending in the worktree. No meaningful behavioral RED test applies to this documentation-only change; no runtime tests were run. Full memory mirror readback is checked separately.

### CP01 — 2026-10-23: planning saved; platform decision next

| Field | Handoff |
|---|---|
| Completed | Distribution-wide roadmap established; delivery-led navigation approved; candidate signing and stable promotion responsibilities separated. Original vision and historical plans preserved. This completes planning work only, not product acceptance |
| Evidence | Parent E1 and child E1/E2 qualify historical structural checks. The simplification passed ID/link/status/whitespace checks and full mirror readback (session summary 4466). No boot, package, installation or publication runtime proof was produced |
| Active selection | R1 -> F01 -> cli-mvp/D1. Detailed task authority: `odd/tasks/cli-mvp.md`; T1-T8 remain planned at this checkpoint |
| Pending decision | D1 is the sole home for the first delivery's architecture, firmware, boot artifact and persistence boundary. Values remain undecided; F06 need not be expanded first |
| Exact next step | Resume planning at D1, explain the reuse-oriented proposal and ask one focused product question. Record the user's answer in the child Log and D1 before refining dependent T1. Do not start implementation from this checkpoint |
| Retained scope | Complete distro for supported bare metal, VM and containers; CLI first slice is not the destination. Later named children and unresolved choices remain in the parent catalog; do not regenerate their plans |
| Authorization | Save/reconcile planning and checkpoints only. No code changes, builds, disk operations, credentials, commits, push, release or deployment authorized |
| Repository snapshot | Herdr feature worktree, branch `feat/distro-quality-stack`, HEAD `1e7ba6716a85ea240cd25f4a2e4b392327c3ef8e`. `odd/roadmap.md` and `odd/tasks/cli-mvp.md` are untracked local files; tracked files unchanged. They are not backed up by a Git commit or push |
| Recovery locators | Parent: `odd/roadmap.md`, project `maquilinux`, topic `odd/maqui-distribution/roadmap`, observation 4459. Child: `odd/tasks/cli-mvp.md`, topic `odd/cli-mvp/tasks`, observation 4456. Read full bodies, not search previews; verify local state before reuse |

CP01 is the first explicit checkpoint, not the start of the project. Prior research, decisions and evidence remain linked above. Its final mirror synchronization is confirmed by readback outside this file to avoid a self-referential write loop.

### CP02 — 2026-10-23: executive view and dependency map saved

| Field | Handoff |
|---|---|
| User approval | "oka", accepting the proposed executive brief and dependency view; full request is preserved in child L9. Documentation only |
| Completed | Added the executive route/file map here and a derived dependency/parallelism view in F01. Preserved existing feature/task IDs, task dependencies and CP01 history; no additional task ledger or speculative task breakdown |
| Evidence boundary | Documentation readback and structural checks only; no runtime proof, build or parallel execution. Final mirror synchronization is checked separately against both full documents |
| Active selection | Still R1 -> F01 -> cli-mvp/D1. Child T1-T8 remain planned, not ready for concurrent writing |
| Exact next step | Resolve D1's first-delivery platform boundary with the user. Then refine the next authorized task's outcome, files, resource ownership and checks; do not decompose all future features |
| Parallelism | T2/T3, T4/T5 and T6/T7 are possible pairs after their respective prerequisites, not scheduled waves. Exact disjoint edit surfaces and isolated mutable resources have not been established |
| Authorization and repository | Planning/persistence only. Branch `feat/distro-quality-stack`, HEAD `1e7ba6716a85ea240cd25f4a2e4b392327c3ef8e`; parent and child remain untracked, without commit/push backup. No implementation, build, credentials or deployment authorized |
| Recovery locators | Same parent observation 4459 at `odd/maqui-distribution/roadmap` and child 4456 at `odd/cli-mvp/tasks`, project `maquilinux`. Reconcile current files and full mirrors; do not restart research or duplicate evidence |

### CP03 — 2026-10-23: autonomy reconciled; baseline artifact missing

Routine reversible progress is now authorized by the user's instruction recorded verbatim in child L10 and Engram 4471. CP01/CP02 preserve the older planning-only boundary as history, not current policy. No stage, commit, push, credentials, shared-rootfs mutation or production action is authorized by this checkpoint.

Resume R1 -> F01 -> T1 using D1 and child E3. D1 selects a reversible x86_64 BIOS/live-ISO qualification target, not production support. Host QEMU and KVM permissions were checked, but no ISO exists in the worktree and the documented public directory returned HTTP 404. T1 remains blocked on an identified artifact; no boot was attempted and no defect was reproduced. Obtain an existing artifact with provenance/checksum, then perform a bounded isolated boot; do not rebuild against the shared rootfs or fix a static hypothesis blindly.

Branch and HEAD remain `feat/distro-quality-stack` / `1e7ba6716a85ea240cd25f4a2e4b392327c3ef8e`. Only the two untracked planning documents changed; no implementation, build or delivery occurred. Recovery uses the same full mirrors 4459 and 4456. Structural checks and full mirror readback are recorded separately; no runtime acceptance is implied.

### CP04 — 2026-10-23: runner and rootfs lifecycle inspected

The user authorized read-only SSH inspection of the existing runner host, filesystem production process and disk partitions, with findings persisted here and in Engram. Connection details remain outside these portable documents. No recovery or disk-use authority follows.

Resume R1 -> F01 -> T1 at child L13-L15/E4-E5. The host has a base rootfs, active overlay and April-June backup archives, but no ISO was confirmed in the bounded locations. The public tree still contains April rootfs archives, not a current ISO. T1 remains blocked on an identified boot artifact; historical archives and mounted filesystems are not boot/provenance proof.

The runner is a user service in an observed restart loop: its startup script reports the configured runner directory missing. Remote checkout `f4745fc` has local changes and differs from this worktree; do not overwrite or update it. Disk inventory found unmounted partitions, but their purpose and contents are unverified. The live rootfs and workspace bind mount use the host system filesystem, not a separately confirmed Maqui installation partition.

Next safe work is read-only archive/base inventory and provenance reconciliation to select an isolated qualification input. Runner repair is a separate operational decision and may require registration credentials; do not install/register/restart it automatically. Do not mount or format the discovered disks. No runtime acceptance, build, service change, commit or publication occurred. This turn edited only the two ODD documents; concurrent `AGENTS.md` and `.agents/skills/` work was observed and preserved. Mirrors remain 4459/4456; structural and full-text readback checks apply to this update.

### CP05 — 2026-10-23: runner recovery is an explicit task

User correction is recorded verbatim in child L16. Existing-runner recovery and qualification now have stable task ID `cli-mvp/T9`, with acceptance and authorization prerequisites in the authoritative child ledger. T3's live CI proof and T8's integrated rehearsal depend on it; routine local investigation remains independent. Rootfs provenance and partition attribution stay in T1, without authorizing disk use. T9 is blocked pending scoped operational recovery authorization, not complete because its cause was found. No repair, service action or credential access occurred. Resume CP04's existing evidence, then T1's safe inventory or T9's recovery preparation; do not repeat the host exploration. Mirrors remain 4459/4456.

### CP06 — 2026-10-23: archive checks complete; isolated image preparation next

Child E6-E7 retain exact hashes and bounded integrity/structure results: the public April rootfs and May runner backup passed complete compression/tar scans with stable source metadata. The public copy includes kernel and live initramfs; the May archive has the kernel but no boot initramfs. The tested June backup is truncated and rejected. Four link targets in each valid archive require confined extraction handling; nothing was extracted. These checks establish neither authenticated provenance nor guest boot.

T1 now owns the next bounded unit: define an isolated image-build workspace/tooling and the required environment/privilege scope before assembly. No ISO exists in the bounded inspected locations, and the current builder uses the shared chroot; do not execute it against that state or silently install host tools. T9 runner recovery remains a separate authorization gate, not a prerequisite for safe local preparation. No new milestones are verified. Resume the retained evidence instead of rescanning valid archives unless source metadata changes. Parent/child mirrors remain 4459/4456; no commits, builds, service changes, disk operations or publication occurred.

### CP07 — 2026-10-23: isolated build prepared; compression budget exhausted

User authorized disposable image preparation in child L19. Verified backup behavior is narrower than automatic before/after protection: package CI has conditional best-effort base snapshots; the ISO path has no matching hooks and base snapshots omit overlay changes. The verified archive remains unchanged as the input; no restore was attempted.

T1/E8 records pinned transient tools, exact boot-member hashes, kernel built-in drivers and supported live-root layout. The scratch environment and logs are retained at `/tmp/opencode/maqui-r1-build-hpPUis`; no full rootfs was extracted. The single two-CPU/512 MiB SquashFS attempt reached its 600-second timeout (exit 124), with no final image left. Therefore no ISO or guest acceptance exists. T1 is blocked on a revised attempt budget, not on missing kernel drivers or permission to create the disposable environment. Resume L20 with one explicitly budgeted attempt; reuse prepared evidence rather than starting exploration again. T9 remains a separate operational recovery gate. Shared rootfs, partitions, runner, source code and profiles were untouched; no commit or publication. Mirrors remain 4459/4456.

### CP08 — 2026-10-23: disposable ISO reaches guest login

User resumed in child L21. The second bounded assembly succeeded; independent BIOS/KVM execution reached Maqui login. Child E9 owns artifact hashes, configuration and logs. T1's narrow baseline is verified; M1 is not: guest commands, networking and clean shutdown remain untested. The harness result does not certify the original mql builder, trusted provenance, package signatures or broader platforms.

T2 now needs a scoped test-access decision before modifying guest authentication. Propose a separate disposable derivative; preserve the verified ISO and never inspect/guess credentials. T9 still owns runner recovery. The previous truncated child mirror was repaired by shortening duplicated operating prose, preserving user quotes, IDs and historical Log; full readback must match after each save. Shared rootfs/disks/runner/source stayed untouched. No Git delivery or publication. Resume R1 -> F01 -> T2 using E9, not a fresh build investigation.

### CP09 — 2026-10-23: asynchronous convention saved; implementation paused

User request (verbatim): "bien agreguemos esto nuevo que t comento para futuras sesiones. como hablamos antes de no perder contexto". Recorded the researched native asynchronous execution convention in the shared continuation rules, not a new implementation feature. Long authorized jobs should leave the parent available, retain identity/logs/results and use independent verification; parallelism requires isolated resources. No command/plugin/service configuration was installed or changed.

Maqui remains on the user-requested standby. Product evidence is unchanged from CP08 and child E9: baseline ISO reaches login; guest commands, network, clean shutdown and trust remain pending. After explicit resume, continue T2's scoped access decision; T9 recovery remains separate. Parent mirror 4459 is updated; unchanged child mirror 4456 remains authoritative and is near its 50,000-byte limit. Check encoded size and full readback before future saves; never silently truncate history. No build, guest run, commit or publication was started by this documentation update.

### CP10 — 2026-10-23: console-only test derivative authorized

User resumed with "ya continua", then answered "si" to temporary root console access only in a separate disposable copy, preserving credentials and host/disks/runner. Child L23 owns the authorization and T2 is in progress. The verified E9 ISO stays immutable; first test derivative has no NIC, host shares or writable disks. Test-only serial agetty configuration lives in the guest RAM overlay, not password files or the base artifact. Scope and injected initramfs entries must be independently checked before guest execution; command/shutdown evidence is still pending.

Background assembly was launched once as `ses_e95870a65ffecrRH6O5QuDXAW9`. Its completion notification and returned artifact identity must be reconciled before another launch; start acknowledgement is not completion. Parent remains available. No runner repair, shared-rootfs change or publication follows from console-test authorization. Mirrors remain 4459/4456; child is near its size limit. Retain task status and terminal evidence there without silent truncation.

### CP11 — 2026-10-23: fixture alignment defect; bounded correction running

T2's first offline derivative probe failed to activate the test console: the kernel rejected the appended initramfs payload. E10/L24 retain hashes, logs and the exact cause: an uncompressed CPIO header at an offset not divisible by four. This is a fixture defect, not evidence of a regression in the E9 base ISO. No credentials or guest commands were used; host termination does not prove clean shutdown.

One scoped correction adds three zero bytes before the unchanged payload in a separate staging tree. Structural proof went RED to GREEN; corrected assembly shell `sh_16a8326e6001tJ2jcdhcb8YdUj` exited 0. Independent worker `ses_e958375bbffejXDlcaaxllyLxo` now rechecks only the fixture blocker and intended console/command/shutdown acceptance. Await its terminal notification; do not duplicate work or broaden authentication scope. No shared-state, runner, network or publication changes. Mirrors remain 4459/4456.

### CP12 — 2026-10-23: alignment resolved; new hook dependency needs decision

Independent recheck completed. Child E11 confirms aligned initramfs loading, then a new failure: chmod is unavailable inside the initramfs. No guest commands or clean shutdown were proved. T2 remains blocked; no job is awaiting a terminal result. The proposed next scoped correction removes redundant chmod and proves the mode produced under umask 077 before one guest recheck. It requires a user decision because the previous bounded correction has been consumed; do not loop automatically. Preserve both fixture variants and E9 baseline. T9 and network/trust work remain separate; no shared-state change or publication occurred. Mirrors remain 4459/4456.

### CP13 — 2026-10-23: additional scoped correction authorized

User answered "continua" to chmod removal, mode proof and one offline recheck (child L25). Empty-PATH test went RED to GREEN, mode 0600 and unchanged-file rejection proved. Corrected hook removes only chmod; previous fixtures/E9 preserved. Assembly `sh_16a918109001hEYrBhZKS2jMvz` exited 0. Independent worker `ses_e958375bbffejXDlcaaxllyLxo` now performs one offline recheck; await terminal notification, do not duplicate it. No network, credentials, host disks, runner repair, publication or automatic retry loop authorized. Mirrors remain 4459/4456.

### CP14 — 2026-10-23: root command proved; harness parser blocked

E12 confirms successful hook, root autologin and UID 0 with exit 0. Probe parser stalled after that command; kernel/runlevel/guest-mode and clean shutdown remain unproved. No job remains active. Further parser-only correction and one offline probe need decision; preserve the verified fixture without rebuilding. Network/trust/runner remain separate. Parent checked serial digest and actual result lines; mirrors 4459/4456 retain evidence.

### CP15 — 2026-10-23: parser-only correction authorized

User answered "si" to parser-only correction and one offline probe (L26). Retained scratch harness passes recorded-log/CRLF/echo tests; unchanged ISO. Independent worker `ses_e958375bbffejXDlcaaxllyLxo` inspects then runs once, with 180-second guest bound. Await terminal notification; no rebuild, network or broader change authorized. Mirrors 4459/4456.

### CP16 — 2026-10-23: offline guest commands and shutdown verified

E13: UID/kernel/runlevel/mode checks passed, natural poweroff/exit 0 in 34.58s; parent checked serial/hash. Unmount warning retained. No active job. T2/M1 remain incomplete: network/trust/original builder unproved. Next: scope networking separately, without credentials, host disks, runner changes or publication. Mirrors 4459/4456.

### CP17 — 2026-10-23: routine disposable NAT tests authorized

User said "siempre autorizado" (L27): standing permission for routine disposable NAT tests without shares/credentials, not delivery/services/runner/persistent installs. One unchanged-ISO DHCP/route/DNS/public HTTPS probe runs via independent worker `ses_e958375bbffejXDlcaaxllyLxo`, 180-second guest bound. Await terminal notification; no host network changes or package installs. Mirrors 4459/4456.

### CP18 — 2026-10-23: network readiness diagnosis

E14: no IPv4 address/default route; DNS/HTTPS not reached. Parent confirmed hash and e1000/eth0 detection. L28 launches one read-only guest NIC/DHCP/OpenRC diagnostic via `ses_e958375bbffejXDlcaaxllyLxo` under standing L27 permission, no repair/install. Await terminal result; preserve E13 offline success. Mirrors 4459/4456.

### CP19 — 2026-10-23: guest DHCP activation experiment; lossless mirror capacity

E15 confirms eth0 DOWN with e1000, dhcpcd installed, network started but DHCP not enabled in default runlevel; diagnostic shutdown completed. Parent inspected immutable service scripts: generic network does not auto-DHCP, existing dhcpcd service raises interfaces. L29 authorizes one guest-RAM-only activation experiment under standing routine NAT scope, not persistent enablement or a host-service change. Worker `ses_e958375bbffejXDlcaaxllyLxo` runs once; await terminal notification. Even success does not prove automatic network boot.

Parent/child mirror topics and observation IDs remain 4459/4456. To preserve full growing documents rather than trim more prose/history, current mirrors use the lossless gzip+base64 envelope specified above. Both decoded SHA-256 and exact encoded readback must match before claiming synchronization. Local Markdown remains uncompressed and authoritative; no source/ISO/credential/publication mutation follows from storage encoding.

### CP20 — 2026-10-23: DHCP interface discovery hypothesis

E16: manual guest DHCP service startup returned success without usable interfaces; network still unproved. L30 records upstream udev-initialization gate and actual guest plugin presence, not a confirmed missing-daemon cause. One version-pinned guest-RAM nodev experiment runs via `ses_e958375bbffejXDlcaaxllyLxo` under standing L27 permission; await terminal notification. No source/ISO/package changes or automatic network-boot claim. Keep T2/M1 incomplete; preserve E13 offline success. Mirrors 4459/4456 remain full lossless encoded documents per capacity contract.

### CP21 — 2026-10-23: explicit discovery differs from manager mode

E17 confirms guest dhcpcd 10.0.6 and explicit TEST DHCP offer, not lease application. Prior harness incorrectly demanded a specific failure log and never reached nodev; no claim it was tested. Parent source inspection explains manager-only plugin loading. L31 starts one neutral manager-debug/ordinary-explicit-DHCP experiment via `ses_e958375bbffejXDlcaaxllyLxo`, under standing disposable NAT scope. Await terminal notification. No source/ISO/config/package changes; applied route/DNS/TLS/automatic boot still unproved. Mirrors 4459/4456 remain full lossless encoded copies.

### CP22 — 2026-10-23: manual guest network works; TLS fails

E18 confirms explicit DHCP lease, route and guest DNS. Manager debug confirms udev initialization waiting; exact boot-readiness cause still unresolved. HTTPS certificate validation failed, no bypass. No normal shutdown in that failed run; E13 offline poweroff proof remains scoped to its own run. L32 explorer `ses_e954344e1ffePPlP3p52h1RU4X` maps udev boot and CA trust paths read-only; no guest job currently active. Await exploration completion, spotcheck before correction. No source/ISO/package/host changes. T2/M1 remain incomplete; mirrors 4459/4456 retain full encoded documents.

### CP23 — 2026-10-23: image preparation gap, not another network retry

E19: actual image lacks OpenRC udev entry and expected default CA bundle/symlink; no alternate usable CA store established. Manual DHCP/DNS E18 remains valid, automatic boot/TLS incomplete. Stop blind guest retries; next proposed scope is isolated packaging/image preparation and requalification, never shared-rootfs/host/runner repair or publication. No active job.

L33 preserves an agent memory incident: explorer summary overwrote child mirror, archived as 4517; prior known-hash local document restored mirror exactly before this update. Local files/history intact. Canonical mirrors 4459/4456 are now explicitly parent-owned, full lossless encoding retained. This checkpoint and E19 require final full encoded readback before synchronized handoff.

### CP24 — 2026-10-23: packaging corrected; isolated builds/checks active

User answered "si" to new isolated packaging/image scope (L34). E20 records RED-to-GREEN source checks, scoped spec/docs lint and preserved compatibility paths. Parent wrote three spec changes, one focused test and build documentation inline; no commits. Actual RPM/image qualification is still pending.

L35 tracks build worker `ses_e950d6765ffew3XE2tcg64duTv` and independent verifier `ses_e9510381affe8ODYWEPn7l08re`, both background. Earlier verifier authentication failure produced no verdict; no credentials were renewed. Build root is exclusively `/tmp/opencode/maqui-r1b-build-re2Pru/` with private namespaces/read-only lower/new upper/minimal devices, never shared rootfs/runner or Docker privileged mode. Forecast: up to 30 minutes per udev build, two compile jobs; stop dependent work on missing sources/dependencies/failure. No install/image assembly until these results are checked. RDD on/global observed, source review pending; original ISOs preserved. Reconcile terminal notifications before advancing. Mirrors remain full lossless copies at 4459/4456.

### CP25 — 2026-10-23: independent packaging checks passed; build pending

E21 confirms baseline RED/candidate GREEN, scoped lint, API support and unchanged compatibility paths in fresh scratch; no packaging-subset blockers. Parent spotcheck passed. This is not full S2/S3/T2/M1 completion. Only isolated RPM build worker `ses_e950d6765ffew3XE2tcg64duTv` remains active; wait terminal notification, never duplicate/poll. No RPM install/new image yet. Source/native review and runtime image checks remain pending, Bats runner unavailable. Original ISOs/shared rootfs/runner untouched; no commits/publication. Mirrors 4459/4456 retain full encoded history.

### CP26 — 2026-10-23: sources prepared; build result not yet established

E22 records that the build actor ended with a plan, not build evidence. Parent confirmed retained sources/backup manifests, no RPM/log outputs, no matching active process or host-visible mount. L36 resumes the same session `ses_e950d6765ffew3XE2tcg64duTv` from prepared inputs, without repeating downloads or assuming an earlier build. Wait its terminal result; launch is not proof of compilation. E21 source verification stays valid. L35 isolation/no-install gates remain; no shared rootfs/runner/image/publication changes. Mirrors 4459/4456 retain full lossless history.

### CP27 — 2026-10-23: RPMs exist; metadata validation not complete

E23 records three parent-hashed RPM outputs, udev's retained build exit and an invalid postcheck using host paths inside chroot. The actor's malformed final response is not acceptance evidence. Parent saw no remaining matching processes, host-visible mounts or loop associations. No rebuild/install/new image.

L37 fresh worker `ses_e94d65754ffeCpTfM7ya1SCpVB` checks retained artifacts/source parity safely and reports missing proof honestly. Await terminal notification; do not resume the previous actor or duplicate builds. RPM metadata/FHS, per-package exit logs where retained, source/native review and image acceptance remain pending. Mirrors 4459/4456 retain complete encoded documents; no shared rootfs/runner/publication or credential changes.

### CP28 — 2026-10-23: artifact proof unavailable; dependent work stopped

E24/L38 record that the fresh inspector also returned no usable verdict and left only an unverified check script, no result logs. Parent confirmed zero related processes and host-visible mounts. Three E23 RPMs and all source/backup/build evidence remain preserved; no rebuild, install or new image follows from file presence or a swallowed postcheck exit.

One blocked result remains: recover trustworthy read-only artifact/source-parity/metadata/FHS proof before installation/assembly. Standing permissions remain intact; the blocker is evidence, not consent for routine tests. No active worker. Preserve E21 source verification and original ISOs; native review/Bats/image acceptance pending. Do not resume the malformed actor or execute retained scripts without inspection. Mirrors 4459/4456 retain full encoded history.

### CP29 — 2026-10-23: direct read-only RPM validation resumed

User said "dale" (L39). Parent proved three copied spec hashes match; no rebuild/install or abandoned-script execution. Native background shell `sh_16b715d1f001pOeeIQw5twMiaw` queries only retained RPMs/FHS using pinned Nix tool substitutions, strict errors, temporary HOME/database/keyring and before/after hashes. No mounts or host package build/profile changes. Wait its terminal notification; do not poll/duplicate. Install/image remain stopped pending actual proof, native review and later runtime acceptance. Mirrors 4459/4456 preserve complete encoded history.

### CP30 — 2026-10-23: artifacts checked; source review terminal; new image next

E26 proves three retained RPMs' identity/digests/ownership/source parity and FHS (3/0), with unsigned status explicit. E27 records native user consent, four admitted immutable reviewers and exact acknowledgement: lineage `review-6c10810d88b84014`, target `sha256:c46415a58447fd363a9ddd69a001159d7f106d38bac0362d66dd7ba22c2b4d0a`, action acknowledged/authority burned. No corrections or delivery authority; advisory findings remain later work, never a reason to reopen this review.

L40 authorizes fresh image preparation only under `/tmp/opencode/maqui-r1b-image-tD89xJ/`: original RO lower, new upper, default-checking offline local DNF transaction, package/link verification, clean export and new BIOS ISO. Never reuse build upper, bypass signature/TLS checks, touch host/shared rootfs/runner, or publish. Forecast up to 40 minutes/two compression workers; independent runtime proof follows assembly. Worker `ses_e9475f377ffeSMK4j23y65uKos` is active in background; await terminal notification, never poll/duplicate. Original images and full mirrors 4459/4456 preserved. Native review lifecycle is terminal; do not issue trailing STATUS/review operations for this unchanged candidate.

### CP31 — 2026-10-23: legacy package ownership blocks installation

E28 confirms DNF rejected two files already owned by installed maquilinux 1-1; failure is not a signature workaround or successful installation. No new ISO/compression; parent confirmed no matching processes or host-visible mounts. All existing RPM/source/review evidence remains scoped and preserved.

L41 read-only migration mapper `ses_e94691606ffeRFLNOibfWCg11x` is the only active worker. Determine actual old payload/config flags/dependencies and complete preservation/rollback before choosing rename/split or proposing edits. No removal/replacefiles/allowerasing or config/security bypass. Wait terminal map, then resolve only a real scope decision. A source correction creates a new candidate; do not reopen consumed review-6c10810d88b84014. Mirrors 4459/4456 retain full encoded history.

### CP32 — 2026-10-23: legacy split is defined; preservation remains unproved

E29 maps installed v1 ownership of FHS/configuration/account files/log seeds and absent filesystem package. Parent source spotcheck confirms the repository already defines filesystem + same-name maquilinux v2 + release, with a versioned filesystem conflict. No blind self-Obsoletes/erase-first accepted. Covering legacy paths does not prove data preservation; config/log handling and filesystem file-list gaps need actual tests/build evidence.

L42 proposes an explicitly scoped fresh-copy transition, missing-family RPM builds and demonstrated packaging preservation fixes, never real-machine migration or credential access. Await one scope confirmation before edits/transactions. No active jobs/new image. Original artifacts, E26 proof and consumed E27 review preserved; new source delta would need new applicable checking. Mirrors 4459/4456 retain full encoded history.

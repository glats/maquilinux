# maqui-build.yaml Schema
<!-- stability: stable | last-reviewed: 2026-07-10 -->

Reference for the optional `maqui-build.yaml` at the repository root.

## Top-level Fields

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `defaults` | object | no | see below |
| `specs` | array | no | [] |
| `jobs` | array | no | [] |

## defaults

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `arch` | array of string | `[x86_64]` | Target architectures |
| `verbose` | boolean | `false` | Enable full build logs |
| `skip_tests` | boolean | `false` | Skip acceptance tests |

## specs

Array of per-spec overrides. Each entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | yes | Spec name without extension (e.g., `<package>`) |
| `arch` | array of string | no | Override default arch |
| `verbose` | boolean | no | Override default verbose |
| `skip_tests` | boolean | no | Override default skip_tests |

All per-spec fields fall back to `defaults` when absent.

## Jobs

Array of trigger definitions (Phase 2). Each entry:

| Field | Type | Description |
|-------|------|-------------|
| `trigger` | string | Event: `push`, `pull_request`, `workflow_dispatch` |
| `branch` | string | Branch filter (e.g., `main`) |
| `mode` | string | `publish` or `validate` |

## Example

```yaml
defaults:
  arch: [x86_64]
  verbose: false
  skip_tests: false

specs:
  - path: <package>
    arch: [x86_64, i686]
    skip_tests: false
  - path: linux
    arch: [x86_64]
    skip_tests: true

jobs:
  - trigger: push
    branch: main
    mode: publish
  - trigger: pull_request
    mode: validate
```

## Related Docs

- [Build Workflow](build-workflow.md) -- pipeline that reads this config

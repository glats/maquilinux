# Build Pipeline Configuration Specification

## Purpose

Define the `maqui-build.yaml` declarative per-spec configuration schema for CI build settings. The config is optional; CI falls back to defaults when absent.

## Requirements

### Requirement: R.6 maqui-build.yaml Schema

The system MUST support an optional `maqui-build.yaml` at the repository root. Each per-spec entry MAY include: `verbose` (bool, default `false`), `skip_tests` (bool, default `false`), `arch` (string or list, default `x86_64`). Unknown fields SHALL emit a warning and be ignored.

#### Scenario: Spec with verbose=true gets verbose logs

- GIVEN `maqui-build.yaml` sets `verbose: true` for a spec
- WHEN that spec is built in CI
- THEN build output includes full rpmbuild logs

#### Scenario: Spec with skip_tests=true skips acceptance tests

- GIVEN `maqui-build.yaml` sets `skip_tests: true` for a spec
- WHEN that spec is built in CI
- THEN acceptance tests (R.1-R.5) are not executed for that package

#### Scenario: Spec with explicit arch overrides default

- GIVEN `maqui-build.yaml` sets `arch: [x86_64, i686]` for a spec
- WHEN that spec is built in CI
- THEN both architectures are built

### Requirement: R.7 CI Reads maqui-build.yaml

The CI pipeline MUST read `maqui-build.yaml` when present and apply per-spec settings during the build loop. Settings from the config override defaults for that spec.

#### Scenario: CI applies per-spec settings during build

- GIVEN `maqui-build.yaml` exists with entries for specific specs
- WHEN CI iterates the build list
- THEN CI reads each spec's config entry before building
- AND applies the configured verbose, skip_tests, and arch settings

### Requirement: R.8 Default Fallback

When `maqui-build.yaml` is absent or a spec has no entry, the system MUST apply defaults: `verbose=false`, `skip_tests=false`, `arch=x86_64`.

#### Scenario: Missing config file uses defaults

- GIVEN no `maqui-build.yaml` exists in the repository
- WHEN CI builds any spec
- THEN all defaults are applied silently

#### Scenario: Missing spec entry uses defaults

- GIVEN `maqui-build.yaml` exists but a given spec has no entry
- WHEN CI builds that spec
- THEN defaults are applied (verbose=false, skip_tests=false, arch=x86_64)

#### Scenario: Invalid config field warns

- GIVEN `maqui-build.yaml` contains an unrecognized field
- WHEN CI parses the config
- THEN a warning is emitted and the field is ignored
- AND the build continues using defaults for the unknown field

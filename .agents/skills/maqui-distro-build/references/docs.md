# Local workflow references

- [Build chain](../../../../scripts/build-chain.sh): inspect ordering, option side effects, installation fallbacks, state and result handling.
- [Package builder](../../../../scripts/build-spec.sh)
- [Build workflow](../../../../agent_docs/build-workflow.md)
- [Dependency resolution](../../../../agent_docs/dependency-resolution.md)
- [Backup flow](../../../../agent_docs/backup-flow.md)
- [Build CI](../../../../.github/workflows/build-rpms-v2.yml): inspect failure propagation separately from chain results.

Read current code before reusing previous observations. Saved status and RPM
existence are evidence inputs, not proof of matching source or accepted output.
Resolve documentation/code disagreements before executing the affected step.

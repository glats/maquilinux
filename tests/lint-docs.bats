#!/usr/bin/env bats
# Tests for `mql lint docs`: repository paths cited in agent docs must exist.

setup() {
    ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
    W="$BATS_TEST_TMPDIR"
}

@test "cited existing paths pass, globs and placeholders are ignored" {
    printf 'See `agent_docs/spec-conventions.md`, `lib/lint.sh`, `SPECS/*.spec`, `SOURCES/<pkg>.tar.xz`.\n' > "$W/ok.md"
    run "$ROOT/mql" lint docs "$W/ok.md"
    [ "$status" -eq 0 ]
    [[ "$output" == *"0 violation(s)"* ]]
}

@test "cited missing path is flagged with its line" {
    printf 'intro\n| `docs/agents/nope-setup.md` | x |\n' > "$W/bad.md"
    run "$ROOT/mql" lint docs "$W/bad.md"
    [ "$status" -eq 1 ]
    [[ "$output" == *"bad.md:2: DOC-PATH: docs/agents/nope-setup.md"* ]]
}

@test "the repository docs have no dead paths" {
    run "$ROOT/mql" lint docs
    [ "$status" -eq 0 ]
}

@test "help points only to documentation that exists" {
    run "$ROOT/mql" help
    for p in $(printf '%s\n' "$output" | grep -oE '(docs|agent_docs)/[A-Za-z0-9_./-]+\.md'); do
        [ -f "$ROOT/$p" ] || { echo "missing: $p"; return 1; }
    done
}

#!/usr/bin/env bats
# Tests for the project agents in .opencode/agents/maqui/ (ODD T5, S1):
# agents call deterministic gates; the gates decide pass/fail.

setup() {
    ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
    AGENTS="$ROOT/.opencode/agents/maqui"
}

frontmatter() {
    awk 'NR==1 && $0=="---" {f=1; next} f && $0=="---" {exit} f' "$1"
}

@test "expected agents exist" {
    for a in spec-steward fhs-auditor release-engineer; do
        [ -f "$AGENTS/$a.md" ] || { echo "missing $a"; return 1; }
    done
}

@test "every agent is a subagent with a description" {
    for f in "$AGENTS"/*.md; do
        fm=$(frontmatter "$f")
        [[ "$fm" == *"mode: subagent"* ]] || { echo "$f: mode"; return 1; }
        [[ "$fm" == *"description: "* ]] || { echo "$f: description"; return 1; }
    done
}

@test "agents use only V2 permission fields" {
    for f in "$AGENTS"/*.md; do
        fm=$(frontmatter "$f")
        for legacy in 'tools:' 'permission:' 'maxSteps:' 'temperature:'; do
            [[ "$fm" != *"$legacy"* ]] || { echo "$f: legacy $legacy"; return 1; }
        done
    done
}

@test "the FHS auditor cannot edit files" {
    fm=$(frontmatter "$AGENTS/fhs-auditor.md")
    [[ "$fm" == *"action: edit"*"effect: deny"* ]]
}

@test "every mql subcommand an agent cites exists" {
    help=$("$ROOT/mql" help)
    for f in "$AGENTS"/*.md; do
        for cmd in $(grep -oE '\bmql [a-z]+' "$f" | awk '{print $2}' | sort -u); do
            grep -qE "^  $cmd\b" <<<"$help" || { echo "$f: mql $cmd"; return 1; }
        done
    done
}

@test "repository paths cited by agents exist" {
    run "$ROOT/mql" lint docs "$AGENTS"/*.md
    [ "$status" -eq 0 ]
}

@test "lint docs scans agent files by default" {
    run "$ROOT/mql" lint docs
    [ "$status" -eq 0 ]
    n=$(git -C "$ROOT" ls-files AGENTS.md CONTRIBUTING.md README.md 'agent_docs/*.md' 'docs/*.md' '.opencode/agents/*.md' | wc -l)
    [[ "$output" == *"lint docs: $n file(s)"* ]]
}

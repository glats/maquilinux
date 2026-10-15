#!/usr/bin/env bats
# Tests for `mql lint endpoints`: machine names and non-canonical endpoints
# must not enter versioned files (S10). Private names are never printed.

setup() {
    ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
    W="$BATS_TEST_TMPDIR/w"
    mkdir -p "$W"
    unset MQL_LINT_PRIVATE_PATTERNS
}

@test "clean file passes" {
    printf 'baseurl=https://repo.maquilinux.org/$releasever\nsee ~/.local/share and /usr/local\n' > "$W/ok.repo"
    run "$ROOT/mql" lint endpoints "$W/ok.repo"
    [ "$status" -eq 0 ]
    [[ "$output" == *"0 violation"* ]]
}

@test "mDNS machine names are flagged without printing the name" {
    printf 'line one\nrsync -a out/ builder7.local:/x\n' > "$W/wf.yml"
    run "$ROOT/mql" lint endpoints "$W/wf.yml"
    [ "$status" -eq 1 ]
    [[ "$output" == *"wf.yml:2: EP-HOST"* ]]
    [[ "$output" != *"builder7"* ]]
}

@test "mql.local config file name is not a machine name" {
    printf 'Copy mql.local.example to mql.local\n' > "$W/doc.md"
    run "$ROOT/mql" lint endpoints "$W/doc.md"
    [ "$status" -eq 0 ]
}

@test "legacy public domain URLs are flagged, contact emails are not" {
    printf 'url: https://repo.glats.org/linux\n* Mon Maqui Linux <dev@glats.org> - 1-1\n' > "$W/x.spec"
    run "$ROOT/mql" lint endpoints "$W/x.spec"
    [ "$status" -eq 1 ]
    [[ "$output" == *"x.spec:1: EP-LEGACY: repo.glats.org"* ]]
    [[ "$output" != *"x.spec:2:"* ]]
}

@test "the lint's own MQL_LINT_ settings are not violations" {
    printf 'MQL_LINT_LEGACY_DOMAINS="glats.org"\nMQL_REPO_URL=https://repo.glats.org/x\n' > "$W/c.conf"
    run "$ROOT/mql" lint endpoints "$W/c.conf"
    [ "$status" -eq 1 ]
    [[ "$output" != *"c.conf:1:"* ]]
    [[ "$output" == *"c.conf:2: EP-LEGACY: repo.glats.org"* ]]
}

@test "private patterns from local config are flagged without printing them" {
    printf 'path=/srv/secretbox/nginx\n' > "$W/s.sh"
    MQL_LINT_PRIVATE_PATTERNS='secretbox' run "$ROOT/mql" lint endpoints "$W/s.sh"
    [ "$status" -eq 1 ]
    [[ "$output" == *"s.sh:1: EP-PRIVATE"* ]]
    [[ "$output" != *"secretbox"* ]]
}

@test "--report lists violations but exits 0" {
    printf 'https://maquiroot.glats.org/latest/\n' > "$W/r.md"
    run "$ROOT/mql" lint endpoints --report "$W/r.md"
    [ "$status" -eq 0 ]
    [[ "$output" == *"r.md:1: EP-LEGACY"* ]]
}

@test "help lists lint endpoints" {
    run "$ROOT/mql" help
    [[ "$output" == *"endpoints [--report]"* ]]
}

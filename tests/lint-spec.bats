#!/usr/bin/env bats
# Tests for `mql lint spec`: Maqui spec conventions (agent_docs/spec-conventions.md).
# Text-only checks, so they run without rpm on any host.

setup() {
    ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
    W="$BATS_TEST_TMPDIR/specs"
    mkdir -p "$W"
    export MQL_RELEASEVER=26.4
}

# good_spec <file> [release]
good_spec() {
    cat > "$1" <<EOF
%global debug_package %{nil}
Name: foo
Version: 1.0
Release: ${2:-1.m264%{?dist\}}
License: MIT
%description
x
%changelog
* Mon Jan 1 2026 Maqui Linux - 1.0-1.m264
- init
EOF
}

@test "conforming spec passes" {
    good_spec "$W/foo.spec"
    run "$ROOT/mql" lint spec "$W/foo.spec"
    [ "$status" -eq 0 ]
    [[ "$output" == *"1 spec(s), 0 violation(s)"* ]]
}

@test "release without dist macro passes" {
    good_spec "$W/fs.spec" "1.m264"
    run "$ROOT/mql" lint spec "$W/fs.spec"
    [ "$status" -eq 0 ]
}

@test "release without the distro tag is rejected" {
    good_spec "$W/bad.spec" "1%{?dist}"
    run "$ROOT/mql" lint spec "$W/bad.spec"
    [ "$status" -eq 1 ]
    [[ "$output" == *"bad.spec: SPEC-RELEASE: 1%{?dist} (want N.m264)"* ]]
}

@test "release tag follows MQL_RELEASEVER" {
    good_spec "$W/next.spec" "1.m2610%{?dist}"
    MQL_RELEASEVER=26.10 run "$ROOT/mql" lint spec "$W/next.spec"
    [ "$status" -eq 0 ]
}

@test "missing debug_package disable is rejected; define form is accepted" {
    good_spec "$W/d.spec"
    sed -i '1d' "$W/d.spec"
    good_spec "$W/e.spec"
    sed -i '1s/.*/%define debug_package        %{nil}/' "$W/e.spec"
    run "$ROOT/mql" lint spec "$W/d.spec" "$W/e.spec"
    [ "$status" -eq 1 ]
    [[ "$output" == *"d.spec: SPEC-DEBUG"* ]]
    [[ "$output" != *"e.spec:"* ]]
}

@test "missing License and changelog are rejected" {
    good_spec "$W/l.spec"
    sed -i '/^License:/d; /^%changelog/,$d' "$W/l.spec"
    run "$ROOT/mql" lint spec "$W/l.spec"
    [ "$status" -eq 1 ]
    [[ "$output" == *"l.spec: SPEC-LICENSE"* ]]
    [[ "$output" == *"l.spec: SPEC-CHANGELOG"* ]]
}

@test "--report lists violations but exits 0, in any position" {
    good_spec "$W/r.spec" "1%{?dist}"
    run "$ROOT/mql" lint spec "$W/r.spec" --report
    [ "$status" -eq 0 ]
    [[ "$output" == *"r.spec: SPEC-RELEASE"* ]]
}

@test "unknown option and missing file fail" {
    run "$ROOT/mql" lint spec --bogus
    [ "$status" -ne 0 ]
    [[ "$output" == *"Unknown option"* ]]
    run "$ROOT/mql" lint spec "$W/nope.spec"
    [ "$status" -ne 0 ]
    [[ "$output" == *"No such file"* ]]
}

@test "help lists lint spec" {
    run "$ROOT/mql" help
    [[ "$output" == *"spec [--report] [spec...]"* ]]
}

#!/usr/bin/env bats
# Tests for `mql lint fhs` (Debian Policy 9.1.1 path rules over RPM file lists).
# A stub `rpm` on PATH serves canned arch and file lists, so no rpm is needed.

setup() {
    ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
    STUB="$BATS_TEST_TMPDIR/bin"
    FIX="$BATS_TEST_TMPDIR/rpms"
    mkdir -p "$STUB" "$FIX"
    cat > "$STUB/rpm" <<'EOF'
#!/usr/bin/env bash
# Stub: rpm -qp --qf '%{ARCH}' <f>  |  rpm -qlp <f>
f="${@: -1}"
case "$1" in
    -qp) cat "$f.arch" ;;
    -qlp) cat "$f.files" ;;
    *) exit 2 ;;
esac
EOF
    chmod +x "$STUB/rpm"
    export PATH="$STUB:$PATH"
}

# make_rpm <name> <arch> <path>...
make_rpm() {
    local name="$1" arch="$2"
    shift 2
    : > "$FIX/$name.rpm"
    printf '%s' "$arch" > "$FIX/$name.rpm.arch"
    printf '%s\n' "$@" > "$FIX/$name.rpm.files"
}

@test "clean x86_64 package passes" {
    make_rpm good x86_64 /usr/bin/foo /usr/lib/x86_64-linux-gnu/libfoo.so.1 /usr/libexec/foo/helper
    run "$ROOT/mql" lint fhs "$FIX/good.rpm"
    [ "$status" -eq 0 ]
    [[ "$output" == *"0 violation"* ]]
}

@test "files under /usr/lib64 are rejected" {
    make_rpm bad x86_64 /usr/lib64/libbar.so.1
    run "$ROOT/mql" lint fhs "$FIX/bad.rpm"
    [ "$status" -eq 1 ]
    [[ "$output" == *"bad.rpm: FHS-USR-LIB64: /usr/lib64/libbar.so.1"* ]]
}

@test "only the dynamic linker may live in /lib64" {
    make_rpm glibc x86_64 /lib64 /lib64/ld-linux-x86-64.so.2
    make_rpm other x86_64 /lib64/libother.so.1
    run "$ROOT/mql" lint fhs "$FIX/glibc.rpm" "$FIX/other.rpm"
    [ "$status" -eq 1 ]
    [[ "$output" == *"other.rpm: FHS-LIB64: /lib64/libother.so.1"* ]]
    [[ "$output" != *"glibc.rpm:"* ]]
}

@test "x86_64 package must not install into the i386 triplet" {
    make_rpm cross x86_64 /usr/lib/i386-linux-gnu/libz.so.1
    run "$ROOT/mql" lint fhs "$FIX/cross.rpm"
    [ "$status" -eq 1 ]
    [[ "$output" == *"cross.rpm: FHS-TRIPLET: /usr/lib/i386-linux-gnu/libz.so.1"* ]]
}

@test "i686 package must not install into the x86_64 triplet" {
    make_rpm cross32 i686 /usr/lib/i386-linux-gnu/libz.so.1 /usr/lib/x86_64-linux-gnu/libz.so.1
    run "$ROOT/mql" lint fhs "$FIX/cross32.rpm"
    [ "$status" -eq 1 ]
    [[ "$output" == *"cross32.rpm: FHS-TRIPLET: /usr/lib/x86_64-linux-gnu/libz.so.1"* ]]
    [[ "$output" != *"FHS-TRIPLET: /usr/lib/i386-linux-gnu"* ]]
}

@test "files under /usr/lib32 are rejected" {
    make_rpm l32 i686 /usr/lib32/libz.so.1
    run "$ROOT/mql" lint fhs "$FIX/l32.rpm"
    [ "$status" -eq 1 ]
    [[ "$output" == *"l32.rpm: FHS-LIB32: /usr/lib32/libz.so.1"* ]]
}

@test "noarch package with a clean layout passes" {
    make_rpm doc noarch /usr/share/doc/foo/README
    run "$ROOT/mql" lint fhs "$FIX/doc.rpm"
    [ "$status" -eq 0 ]
}

@test "unknown lint subcommand fails" {
    run "$ROOT/mql" lint bogus
    [ "$status" -ne 0 ]
    [[ "$output" == *"Unknown lint subcommand"* ]]
}

@test "existing help still lists audit and now lists lint" {
    run "$ROOT/mql" help
    [ "$status" -eq 0 ]
    [[ "$output" == *"audit [options]"* ]]
    [[ "$output" == *"fhs [rpm...]"* ]]
}

@test "lookalike paths are not flagged" {
    make_rpm look x86_64 /usr/lib64x/foo /usr/lib/i386-linux-gnux/a /usr/libexec/h
    run "$ROOT/mql" lint fhs "$FIX/look.rpm"
    [ "$status" -eq 0 ]
}

@test "loader lookalike in /lib64 is rejected" {
    make_rpm ll x86_64 /lib64/ld-linux-x86-64.so.2x
    run "$ROOT/mql" lint fhs "$FIX/ll.rpm"
    [ "$status" -eq 1 ]
}

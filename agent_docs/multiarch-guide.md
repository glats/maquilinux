# Multiarch Guide
<!-- stability: stable | last-reviewed: 2026-10-16 -->

Maqui supports x86_64 with i686 multilib via Debian-style library layout.
Specs that build for both architectures include i686 conditionals following
a consistent pattern (`grep -l '_target_cpu.*i686' SPECS/*.spec` lists them).

## Library Layout

| Architecture | Path | Role |
|-------------|------|------|
| x86_64 | `/usr/lib/x86_64-linux-gnu` | 64-bit libraries |
| i686 | `/usr/lib/i386-linux-gnu` | 32-bit libraries |

Packages install no files under `/usr/lib64` or `/usr/lib32`; the layout is
unified under `/usr/lib`. Those paths, and `/lib64`, exist only as
compatibility symlinks owned by `filesystem` (the loader must resolve at
`/lib64/ld-linux-x86-64.so.2`). `mql lint fhs` enforces the rule on built RPMs.

## Spec Pattern

Every multiarch-capable spec starts with:

```spec
%if "%{_target_cpu}" == "i686"
%global multilibdir /usr/lib/i386-linux-gnu
%global enable_devel 0
%else
%global multilibdir /usr/lib/x86_64-linux-gnu
%global enable_devel 1
%endif
```

## Detecting i686 Support

`mql build --both` detects i686 support by scanning the spec for
`%if "%{_target_cpu}" == "i686"`. If the pattern is present, the spec is
built for both architectures.

## 32-bit Build: Separate Directory

The 32-bit build happens in a copy of the source tree:

```spec
cp -a ../%{name}-%{version} ../%{name}-%{version}-32
pushd ../%{name}-%{version}-32
CC="gcc -m32" CXX="g++ -m32" \
./configure --host=i686-pc-linux-gnu --libdir=/usr/lib/i386-linux-gnu
make
popd
```

## 32-bit Install: Library-Only

32-bit builds strip non-library content. Binaries, headers, and pkgconfig
files are removed:

```spec
%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir}
rm -rf %{buildroot}%{_includedir}
rm -rf %{buildroot}%{_mandir}
rm -rf %{buildroot}%{_libdir}/pkgconfig
%endif
```

## Architecture Restriction

Specs that build for i686 should declare the restriction below. It is not yet
enforced and many i686 specs still lack it (`grep -L ExclusiveArch SPECS/*.spec`):

```spec
ExclusiveArch: x86_64 i686
```

ARM64 and other architectures are not yet supported.

## Related Docs

- [Spec Conventions](spec-conventions.md) -- the full spec format
- [Build Workflow](build-workflow.md) -- how --both works in practice

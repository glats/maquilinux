# Spec Conventions
<!-- stability: stable | last-reviewed: 2026-07-10 -->

All RPM spec files follow these conventions. They are the single source of
truth for package definitions.

## Header Fields

| Field | Convention |
|-------|-----------|
| Release | `1.m264` (m264 = Maqui Linux 26.4) |
| License | As declared by upstream |
| URL | Upstream project URL |
| Source0 | `%{name}-%{version}.tar.xz` (or .gz, .bz2) |

## Required Disables

```spec
%global debug_package %{nil}
```

Debug packages are disabled globally. Do not re-enable.

## Multiarch Macros

100+ specs include i686 conditionals. The standard pattern:

```spec
%if "%{_target_cpu}" == "i686"
%global multilibdir /usr/lib/i386-linux-gnu
%global enable_devel 0
%else
%global multilibdir /usr/lib/x86_64-linux-gnu
%global enable_devel 1
%endif
```

## Library Directories

| Arch | Path |
|------|------|
| x86_64 | `/usr/lib/x86_64-linux-gnu` |
| i686 | `/usr/lib/i386-linux-gnu` |

Do NOT use `/usr/lib64` or `/usr/lib32`. These paths are rejected.

## 32-bit Build Pattern

For libraries that support multiarch, build in a separate directory:

```spec
%build
# 64-bit
./configure --libdir=%{multilibdir}
make

# 32-bit (copy tree, build with -m32)
cp -a ../%{name}-%{version} ../%{name}-%{version}-32
pushd ../%{name}-%{version}-32
CC="gcc -m32" CXX="g++ -m32" \
./configure --host=i686-pc-linux-gnu --libdir=/usr/lib/i386-linux-gnu
make
popd
```

## 32-bit Install Stripping

For 32-bit builds, ship only libraries:

```spec
%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir}
rm -rf %{buildroot}%{_includedir}
rm -rf %{buildroot}%{_libdir}/pkgconfig
%endif
```

## Architecture Restrictions

```spec
ExclusiveArch: x86_64 i686
```

## Related Docs

- [Build Workflow](build-workflow.md) -- the build pipeline
- [Multiarch Guide](multiarch-guide.md) -- detailed multiarch patterns

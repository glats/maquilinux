# Maquilinux RPM Spec Template (Gen3)

This document describes the standard pattern for Maquilinux RPM specs.
All new specs and updates to existing specs should follow this pattern.

## Required Header Block

```spec
%define pkg_version X.Y.Z

# Disable debuginfo in bootstrap/minimal chroot
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

# Multiarch configuration
%if "%{_target_cpu}" == "i686"
%global pkg_multilibdir /usr/lib/i386-linux-gnu
%global pkg_enable_devel 0
%else
%global pkg_multilibdir /usr/lib/x86_64-linux-gnu
%global pkg_enable_devel 1
%endif

Name:           pkgname
Version:        %{pkg_version}
Release:        1.m264%{?dist}
Summary:        Short description

# Explicit Provides for shared library sonames (required for bootstrap)
%if "%{_target_cpu}" == "x86_64"
Provides:       libpkgname.so.N()(64bit)
%endif

License:        LICENSE
URL:            https://example.com
Source0:        https://example.com/pkgname-%{version}.tar.xz
```

## Subpackage Definition (-devel)

For libraries, always create a real `-devel` subpackage on x86_64:

```spec
%if %{pkg_enable_devel}
%package devel
Summary:        Development files for pkgname
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, CMake configuration files, and the
unversioned shared library symlink for developing against pkgname.
%endif
```

## Build Section

```spec
%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
export PKG_CONFIG_LIBDIR="/usr/lib/i386-linux-gnu/pkgconfig:/usr/share/pkgconfig"
CONFIG_HOST=--host=i686-pc-linux-gnu
%else
export PKG_CONFIG_LIBDIR="/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/share/pkgconfig"
CONFIG_HOST=""
%endif

./configure \
    --prefix=%{_prefix} \
    --libdir=%{pkg_multilibdir} \
    --disable-static \
    ${CONFIG_HOST}

make %{?_smp_mflags}
```

## Install Section with Filelist Generation

```spec
%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

# Remove static libraries
rm -fv %{buildroot}%{pkg_multilibdir}/*.a || :
rm -fv %{buildroot}%{pkg_multilibdir}/*.la || :

# i686: prune non-library content (libs-only package)
%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

# Generate file lists with normalization
cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  if [ -d .%{pkg_multilibdir} ]; then
    find .%{pkg_multilibdir} -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/pkg-files.list
%else
# All files
find . \( -type f -o -type l \) | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/pkg-all.list

# Runtime files: versioned shared libs, docs, man pages
{
  if [ -d .%{pkg_multilibdir} ]; then
    find .%{pkg_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libpkgname.so.*'
  fi
  if [ -d ./usr/share/doc ]; then
    find ./usr/share/doc -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/pkg-runtime.list

%if %{pkg_enable_devel}
# Development files: headers, pkgconfig, cmake, unversioned .so symlink
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  if [ -d .%{pkg_multilibdir} ]; then
    find .%{pkg_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libpkgname.so'
    if [ -d .%{pkg_multilibdir}/pkgconfig ]; then
      find .%{pkg_multilibdir}/pkgconfig -type f -o -type l
    fi
    if [ -d .%{pkg_multilibdir}/cmake ]; then
      find .%{pkg_multilibdir}/cmake -type f -o -type l
    fi
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/pkg-devel.list
%endif
%endif
```

## Files Sections

```spec
%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/pkg-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/pkg-runtime.list
%defattr(-,root,root,-)

%if %{pkg_enable_devel}
%files devel -f %{_builddir}/pkg-devel.list
%defattr(-,root,root,-)
%endif
%endif
```

## Post-install Scripts (for shared libraries)

```spec
%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig
```

## Checklist for New/Updated Specs

- [ ] `%global debug_package %{nil}` and related disabled
- [ ] `%global pkg_multilibdir` defined correctly for both arches
- [ ] `%global pkg_enable_devel` conditional for i686 vs x86_64
- [ ] Explicit `Provides: libX.so.N()(64bit)` for x86_64 (bootstrap requirement)
- [ ] Real `%package devel` subpackage (not just `Provides: X-devel`)
- [ ] Filelist normalization with `sed -e 's|//\+|/|g'` and `sort -u`
- [ ] Runtime vs devel file separation
- [ ] `%post/%postun ldconfig` for packages with shared libraries
- [ ] Static libraries removed (`.a`, `.la`)
- [ ] i686 build prunes non-library content
- [ ] `rm -f %{buildroot}/usr/share/info/dir` to avoid conflicts

## Common Soname Provides Reference

| Package | Soname Provides |
|---------|-----------------|
| zlib | `libz.so.1()(64bit)` |
| bzip2 | `libbz2.so.1.0()(64bit)` |
| xz | `liblzma.so.5()(64bit)` |
| zstd | `libzstd.so.1()(64bit)` |
| lz4 | `liblz4.so.1()(64bit)` |
| ncurses | `libncursesw.so.6()(64bit)` |
| readline | `libreadline.so.8()(64bit)` |
| gmp | `libgmp.so.10()(64bit)` |
| mpfr | `libmpfr.so.6()(64bit)` |
| mpc | `libmpc.so.3()(64bit)` |
| libffi | `libffi.so.8()(64bit)` |
| openssl | `libssl.so.3()(64bit)`, `libcrypto.so.3()(64bit)` |
| sqlite | `libsqlite3.so.0()(64bit)` |
| expat | `libexpat.so.1()(64bit)` |
| libxml2 | `libxml2.so.2()(64bit)` |
| curl | `libcurl.so.4()(64bit)` |
| fmt | `libfmt.so.12()(64bit)` |
| json-c | `libjson-c.so.5()(64bit)` |

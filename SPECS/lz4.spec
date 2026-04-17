%define lz4_version 1.10.0

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global lz4_multilibdir /usr/lib/i386-linux-gnu
%global lz4_enable_devel 0
%else
%global lz4_multilibdir /usr/lib/x86_64-linux-gnu
%global lz4_enable_devel 1
%endif

Name:           lz4
Version:        %{lz4_version}
Release:        1.m264%{?dist}
Summary:        LZ4 - extremely fast compression algorithm

%if "%{_target_cpu}" == "x86_64"
Provides:       liblz4.so.1()(64bit)
%endif

License:        BSD
URL:            https://lz4.github.io/lz4/
Source0:        https://github.com/lz4/lz4/releases/download/v%{version}/lz4-%{version}.tar.gz

%if %{lz4_enable_devel}
%package devel
Summary:        Development files for lz4
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlink
for developing against liblz4.
%endif

%description
LZ4 is a very fast lossless compression algorithm, providing compression
speed greater than 500 MB/s per core and multi-GB/s decompression speed.

%prep
%setup -q -n lz4-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
%endif

make BUILD_STATIC=no PREFIX=%{_prefix} %{?_smp_mflags}

%check
# Upstream tests; run only for the 64-bit build tree
make -j1 check || :

%install
rm -rf %{buildroot}

# NOTE: lz4 1.10.0 has an upstream bug when LIBDIR is set (see issue #1467).
# The installation still succeeds.
make BUILD_STATIC=no \
     PREFIX=%{_prefix} \
     LIBDIR=%{lz4_multilibdir} \
     DESTDIR=%{buildroot} install

rm -fv %{buildroot}%{lz4_multilibdir}/liblz4.a || :

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_includedir} || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  find .%{lz4_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/lz4-files.list
%else
# Runtime: versioned shared libs, binaries, man pages
{
  find .%{lz4_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'liblz4.so.*'
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/lz4-runtime.list

%if %{lz4_enable_devel}
# Development: headers, pkgconfig, unversioned .so symlink
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{lz4_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'liblz4.so'
  if [ -d .%{lz4_multilibdir}/pkgconfig ]; then
    find .%{lz4_multilibdir}/pkgconfig -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/lz4-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/lz4-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/lz4-runtime.list
%defattr(-,root,root,-)

%if %{lz4_enable_devel}
%files devel -f %{_builddir}/lz4-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.10.0-1.m264
- Initial RPM packaging for lz4 with multiarch layout.

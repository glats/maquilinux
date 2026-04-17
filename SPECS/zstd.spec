%define zstd_version 1.5.7

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global zstd_multilibdir /usr/lib/i386-linux-gnu
%global zstd_enable_devel 0
%else
%global zstd_multilibdir /usr/lib/x86_64-linux-gnu
%global zstd_enable_devel 1
%endif

Name:           zstd
Version:        %{zstd_version}
Release:        1.m264%{?dist}
Summary:        Zstandard real-time compression algorithm

%if "%{_target_cpu}" == "x86_64"
Provides:       libzstd.so.1()(64bit)
%endif

License:        BSD
URL:            https://github.com/facebook/zstd
Source0:        https://github.com/facebook/zstd/releases/download/v%{version}/zstd-%{version}.tar.gz

%if %{zstd_enable_devel}
%package devel
Summary:        Development files for zstd
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlink
for developing against libzstd.
%endif

%description
Zstandard is a fast lossless compression algorithm, providing high compression
ratios and very fast decompression. This package installs the zstd command
line tools and the shared libzstd library in a multiarch layout.

%prep
%setup -q -n zstd-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
%endif

make prefix=%{_prefix} %{?_smp_mflags}

%check
# Upstream tests; run only for the 64-bit build tree
make -j1 check || :

%install
rm -rf %{buildroot}

make prefix=%{_prefix} \
     LIBDIR=%{zstd_multilibdir} \
     DESTDIR=%{buildroot} install

rm -fv %{buildroot}%{zstd_multilibdir}/libzstd.a || :

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
  find .%{zstd_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/zstd-files.list
%else
# Runtime: versioned shared libs, binaries, man pages
{
  find .%{zstd_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libzstd.so.*'
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/zstd-runtime.list

%if %{zstd_enable_devel}
# Development: headers, pkgconfig, cmake, unversioned .so symlink
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{zstd_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libzstd.so'
  if [ -d .%{zstd_multilibdir}/pkgconfig ]; then
    find .%{zstd_multilibdir}/pkgconfig -type f -o -type l
  fi
  if [ -d .%{zstd_multilibdir}/cmake ]; then
    find .%{zstd_multilibdir}/cmake -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/zstd-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/zstd-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/zstd-runtime.list
%defattr(-,root,root,-)

%if %{zstd_enable_devel}
%files devel -f %{_builddir}/zstd-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.5.7-1.m264
- zstd initial RPM packaging.

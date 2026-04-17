%define xz_version 5.8.1

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global xz_multilibdir /usr/lib/i386-linux-gnu
%global xz_enable_devel 0
%else
%global xz_multilibdir /usr/lib/x86_64-linux-gnu
%global xz_enable_devel 1
%endif

Name:           xz
Version:        %{xz_version}
Release:        1.m264%{?dist}
Summary:        XZ Utils - general-purpose data compression toolkit

%if "%{_target_cpu}" == "x86_64"
Provides:       liblzma.so.5()(64bit)
%endif

License:        Public Domain and GPLv2+
URL:            https://tukaani.org/xz/
Source0:        https://tukaani.org/xz/xz-%{version}.tar.xz

%if %{xz_enable_devel}
%package devel
Summary:        Development files for xz (liblzma)
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, CMake configuration files, and the
unversioned shared library symlink for developing against liblzma.
%endif

%description
XZ Utils provide high-compression-ratio lossless data compression tools (xz,
xzdec, lzma) and the liblzma library, supporting the LZMA and XZ formats.

%prep
%setup -q -n xz-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
CONFIG_HOST=--host=i686-pc-linux-gnu
%else
CONFIG_HOST=""
%endif

./configure --prefix=%{_prefix} \
            --libdir=%{xz_multilibdir} \
            --disable-static \
            --docdir=%{_datadir}/doc/xz-%{version} \
            ${CONFIG_HOST}

make %{?_smp_mflags}

%check
make check

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

rm -fv %{buildroot}%{xz_multilibdir}/liblzma.a || :
rm -fv %{buildroot}%{xz_multilibdir}/*.la || :

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
  find .%{xz_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/xz-files.list
%else
# Runtime: versioned shared libs, binaries, man pages, docs
{
  find .%{xz_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'liblzma.so.*'
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
  if [ -d ./usr/share/doc ]; then
    find ./usr/share/doc -type f -o -type l
  fi
  if [ -d ./usr/share/locale ]; then
    find ./usr/share/locale -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/xz-runtime.list

%if %{xz_enable_devel}
# Development: headers, pkgconfig, cmake, unversioned .so symlink
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{xz_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'liblzma.so'
  if [ -d .%{xz_multilibdir}/pkgconfig ]; then
    find .%{xz_multilibdir}/pkgconfig -type f -o -type l
  fi
  if [ -d .%{xz_multilibdir}/cmake ]; then
    find .%{xz_multilibdir}/cmake -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/xz-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/xz-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/xz-runtime.list
%defattr(-,root,root,-)

%if %{xz_enable_devel}
%files devel -f %{_builddir}/xz-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 5.8.1-1.m264
- xz initial RPM packaging.

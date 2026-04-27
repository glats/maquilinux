%define pkg_version 1.50

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global pkg_multilibdir /usr/lib/i386-linux-gnu
%global pkg_enable_devel 0
%else
%global pkg_multilibdir /usr/lib/x86_64-linux-gnu
%global pkg_enable_devel 1
%endif

Name:           libgpg-error
Version:        %{pkg_version}
Release:        1.m264%{?dist}
Summary:        Library for error values used by GnuPG components

License:        LGPL-2.1-or-later
URL:            https://www.gnupg.org/related_software/libgpg-error/
Source0:        https://gnupg.org/ftp/gcrypt/libgpg-error/libgpg-error-%{version}.tar.bz2

BuildRequires:  gcc
BuildRequires:  make

%if "%{_target_cpu}" == "x86_64"
Provides:       libgpg-error.so.0()(64bit)
%endif

%description
libgpg-error is a small library with error codes and descriptions shared by all
GnuPG related software. This package is required for building GnuPG, GPGME,
and other GnuPG related software.

%if %{pkg_enable_devel}
%package devel
Summary:        Development files for libgpg-error
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
The libgpg-error-devel package contains libraries and header files for developing
applications that use libgpg-error.
%endif

%prep
%setup -q

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

export CFLAGS="-std=gnu17 ${CFLAGS:-}"

./configure \
    --prefix=%{_prefix} \
    --libdir=%{pkg_multilibdir} \
    --enable-shared \
    --disable-static \
    --enable-install-gpg-error-config \
    ${CONFIG_HOST} \
    CFLAGS="${CFLAGS}"

make %{?_smp_mflags} CFLAGS="${CFLAGS}"

%install
make DESTDIR=%{buildroot} install

rm -fv %{buildroot}%{pkg_multilibdir}/*.la || :
rm -fv %{buildroot}%{pkg_multilibdir}/*.a || :
rm -rf %{buildroot}%{_datadir}/common-lisp || :
rm -rf %{buildroot}%{_datadir}/locale || :
rm -f %{buildroot}/usr/share/info/dir || :

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir}/aclocal || :
rm -rf %{buildroot}%{_infodir} || :
%endif

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  if [ -d .%{pkg_multilibdir} ]; then
    find .%{pkg_multilibdir} -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libgpg-error-files.list
%else
find . \( -type f -o -type l \) | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libgpg-error-all.list

{
  if [ -d .%{pkg_multilibdir} ]; then
    find .%{pkg_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libgpg-error.so.*'
  fi
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -o -type l
  fi
  if [ -d ./usr/share ]; then
    find ./usr/share/libgpg-error -type f -o -type l 2>/dev/null || true
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libgpg-error-runtime.list

%if %{pkg_enable_devel}
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  if [ -d .%{pkg_multilibdir}/pkgconfig ]; then
    find .%{pkg_multilibdir}/pkgconfig -type f -o -type l
  fi
  if [ -d .%{pkg_multilibdir} ]; then
    find .%{pkg_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libgpg-error.so'
  fi
  if [ -d ./usr/share/aclocal ]; then
    find ./usr/share/aclocal -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libgpg-error-devel.list
%endif
%endif

%post
%{_sbindir}/ldconfig || :

%postun
%{_sbindir}/ldconfig || :

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/libgpg-error-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/libgpg-error-runtime.list
%defattr(-,root,root,-)

%if %{pkg_enable_devel}
%files devel -f %{_builddir}/libgpg-error-devel.list
%defattr(-,root,root,-)
%endif
%endif

%changelog
* Sun Apr 19 2026 Maqui Linux <security@maqui-linux.org> - 1.50-1.m264
- Initial build for Maqui Linux 26.4
- Gen3 template: pkg_multilibdir, generated file lists, multiarch
%define libxml2_version 2.15.1

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global libxml2_multilibdir /usr/lib/i386-linux-gnu
%global libxml2_enable_devel 0
%else
%global libxml2_multilibdir /usr/lib/x86_64-linux-gnu
%global libxml2_enable_devel 1
%endif

Name:           libxml2
Version:        %{libxml2_version}
Release:        1.m264%{?dist}
Summary:        XML parsing library

%if "%{_target_cpu}" == "x86_64"
Provides:       libxml2.so.2()(64bit)
%endif

License:        MIT
URL:            https://gitlab.gnome.org/GNOME/libxml2
Source0:        https://download.gnome.org/sources/libxml2/2.15/libxml2-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  pkgconf
BuildRequires:  python3
BuildRequires:  zlib

%description
libxml2 is an XML toolkit implemented in C.

%if %{libxml2_enable_devel}
%package devel
Summary:        Development files for libxml2
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlink
for developing against libxml2.
%endif

%prep
%setup -q -n libxml2-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
export CPPFLAGS="${CPPFLAGS:-} -I/usr/include"
export LDFLAGS="${LDFLAGS:-} -L/usr/lib/i386-linux-gnu"
export PKG_CONFIG_LIBDIR="/usr/lib/i386-linux-gnu/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig"
CONFIG_HOST=--host=i686-pc-linux-gnu
CONFIG_LIBDIR=--libdir=/usr/lib/i386-linux-gnu
%else
export CPPFLAGS="${CPPFLAGS:-} -I/usr/include"
export LDFLAGS="${LDFLAGS:-} -L/usr/lib/x86_64-linux-gnu"
export PKG_CONFIG_LIBDIR="/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig"
CONFIG_HOST=""
CONFIG_LIBDIR=--libdir=/usr/lib/x86_64-linux-gnu
%endif

mkdir -p build
pushd build
../configure \
    --prefix=%{_prefix} \
    ${CONFIG_LIBDIR} \
    ${CONFIG_HOST} \
    --disable-static \
    --without-python \
    --without-lzma \
    --without-icu \
    --without-schematron \
    --without-readline \
    --with-zlib

make %{?_smp_mflags}
popd

%check
:

%install
rm -rf %{buildroot}

pushd build
make DESTDIR=%{buildroot} install
popd

rm -f %{buildroot}%{libxml2_multilibdir}/*.la || :
rm -f %{buildroot}%{libxml2_multilibdir}/*.a || :

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_mandir} || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  if [ -d .%{libxml2_multilibdir} ]; then
    find .%{libxml2_multilibdir} -type f -o -type l
  fi
} | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/libxml2-files.list

test -s %{_builddir}/libxml2-files.list
%else
find . \( -type f -o -type l \) | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/libxml2-all.list

test -s %{_builddir}/libxml2-all.list

%if %{libxml2_enable_devel}
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  if [ -d .%{libxml2_multilibdir} ]; then
    if [ -d .%{libxml2_multilibdir}/pkgconfig ]; then
      find .%{libxml2_multilibdir}/pkgconfig -type f -o -type l
    fi
    if [ -d .%{libxml2_multilibdir}/cmake ]; then
      find .%{libxml2_multilibdir}/cmake -type f -o -type l
    fi
    find .%{libxml2_multilibdir} -maxdepth 1 -type f -name 'libxml2.so'
    find .%{libxml2_multilibdir} -maxdepth 1 -type l -name 'libxml2.so'
  fi
  if [ -f ./usr/bin/xml2-config ]; then
    echo ./usr/bin/xml2-config
  fi
} | sed 's|^\.||' | LC_ALL=C sort -u > %{_builddir}/libxml2-devel.list

test -s %{_builddir}/libxml2-devel.list

grep -F -x -v -f %{_builddir}/libxml2-devel.list %{_builddir}/libxml2-all.list > %{_builddir}/libxml2-runtime.list

test -s %{_builddir}/libxml2-runtime.list
%else
cp %{_builddir}/libxml2-all.list %{_builddir}/libxml2-runtime.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/libxml2-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/libxml2-runtime.list
%defattr(-,root,root,-)

%if %{libxml2_enable_devel}
%files devel -f %{_builddir}/libxml2-devel.list
%defattr(-,root,root,-)
%endif
%endif

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.15.1-1.m264
- Initial libxml2 packaging with runtime and -devel split.

%define sqlite_version 3.51.1

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global sqlite_multilibdir /usr/lib/i386-linux-gnu
%global sqlite_enable_devel 0
%else
%global sqlite_multilibdir /usr/lib/x86_64-linux-gnu
%global sqlite_enable_devel 1
%endif

Name:           sqlite
Version:        %{sqlite_version}
Release:        2.m264%{?dist}
Summary:        Self-contained SQL database engine

%if "%{_target_cpu}" == "x86_64"
Provides:       libsqlite3.so()(64bit)
Provides:       libsqlite3.so.0()(64bit)
%endif

License:        Public Domain
URL:            https://www.sqlite.org/
Source0:        https://www.sqlite.org/2024/sqlite-autoconf-3510100.tar.gz
Source1:        https://www.sqlite.org/2024/sqlite-doc-3510100.tar.xz

%if %{sqlite_enable_devel}
%package devel
Summary:        Development files for sqlite
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlink
for developing against SQLite.
%endif

%description
SQLite is a C library that implements an SQL database engine with no server
and zero configuration.

%prep
%setup -q -n sqlite-autoconf-3510100

# Unpack the documentation alongside the sources
%{__tar} -xf %{SOURCE1} -C ..
mkdir -p doc
cp -a ../sqlite-doc-3510100/* doc/

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
CONFIG_HOST=--host=i686-pc-linux-gnu
%else
CONFIG_HOST=""
%endif

./configure \
    --prefix=%{_prefix} \
    --libdir=%{sqlite_multilibdir} \
    --disable-static \
    --enable-fts4 \
    --enable-fts5 \
    ${CONFIG_HOST} \
    CPPFLAGS="-D SQLITE_ENABLE_COLUMN_METADATA=1 -D SQLITE_ENABLE_UNLOCK_NOTIFY=1 -D SQLITE_ENABLE_DBSTAT_VTAB=1 -D SQLITE_SECURE_DELETE=1"

make %{?_smp_mflags} LDFLAGS.rpath=""

%check
# No upstream test suite per MLFS; skip
:

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_datadir} || :
%else
install -d %{buildroot}%{_datadir}/doc/sqlite-%{version}
cp -a doc/* %{buildroot}%{_datadir}/doc/sqlite-%{version}/
%endif

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  find .%{sqlite_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/sqlite-files.list
%else
# Runtime: versioned shared libs, binaries, man pages, docs
{
  find .%{sqlite_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so.*'
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
  if [ -d ./usr/share/doc ]; then
    find ./usr/share/doc -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/sqlite-runtime.list

%if %{sqlite_enable_devel}
# Development: headers, pkgconfig, unversioned .so symlink
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{sqlite_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so' ! -name '*.so.*'
  if [ -d .%{sqlite_multilibdir}/pkgconfig ]; then
    find .%{sqlite_multilibdir}/pkgconfig -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/sqlite-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/sqlite-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/sqlite-runtime.list
%defattr(-,root,root,-)

%if %{sqlite_enable_devel}
%files devel -f %{_builddir}/sqlite-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 3.51.1-1.m264
- Initial RPM packaging for sqlite.

%define popt_version 1.19

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global popt_multilibdir /usr/lib/i386-linux-gnu
%global popt_enable_devel 0
%else
%global popt_multilibdir /usr/lib/x86_64-linux-gnu
%global popt_enable_devel 1
%endif

Name:           popt
Version:        %{popt_version}
Release:        1.m264%{?dist}
Summary:        Command line option parsing library

%if "%{_target_cpu}" == "x86_64"
Provides:       libpopt.so.0()(64bit)
%endif

License:        MIT
URL:            https://github.com/rpm-software-management/popt
Source0:        https://ftp.osuosl.org/pub/rpm/popt/releases/popt-1.x/popt-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make

%if %{popt_enable_devel}
%package devel
Summary:        Development files for popt
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlink
for developing against popt.
%endif

%description
popt is a C library for parsing command line options, used by RPM and other
software.

%prep
%setup -q -n popt-%{version}

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
    --libdir=%{popt_multilibdir} \
    --disable-static \
    ${CONFIG_HOST}

make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

# Drop libtool archive: it pulls in static deps and isn't needed for RPM builds.
rm -f %{buildroot}%{popt_multilibdir}/libpopt.la

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_datadir} || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  find .%{popt_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/popt-files.list
%else
# Runtime: versioned shared libs, man pages
{
  find .%{popt_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so.*'
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
  if [ -d ./usr/share/locale ]; then
    find ./usr/share/locale -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/popt-runtime.list

%if %{popt_enable_devel}
# Development: headers, pkgconfig, unversioned .so symlink
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{popt_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so' ! -name '*.so.*'
  if [ -d .%{popt_multilibdir}/pkgconfig ]; then
    find .%{popt_multilibdir}/pkgconfig -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/popt-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/popt-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/popt-runtime.list
%defattr(-,root,root,-)

%if %{popt_enable_devel}
%files devel -f %{_builddir}/popt-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.19-1.m264
- popt initial RPM packaging.

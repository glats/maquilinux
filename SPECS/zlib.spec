%define zlib_version 1.3.1

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global zlib_multilibdir /usr/lib/i386-linux-gnu
%global zlib_enable_devel 0
%else
%global zlib_multilibdir /usr/lib/x86_64-linux-gnu
%global zlib_enable_devel 1
%endif

Name:           zlib
Version:        %{zlib_version}
Release:        1.m264%{?dist}
Summary:        Compression and decompression library

%if "%{_target_cpu}" == "x86_64"
Provides:       libz.so.1()(64bit)
%endif

License:        Zlib
URL:            http://zlib.net
Source0:        https://zlib.net/fossils/zlib-%{version}.tar.gz

%if %{zlib_enable_devel}
%package devel
Summary:        Development files for zlib
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlink
for developing against zlib.
%endif

%description
The Zlib package contains compression and decompression routines used by some programs.

%prep
%setup -q -n %{name}-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
%endif

./configure --prefix=%{_prefix} \
            --libdir=%{zlib_multilibdir}

make %{?_smp_mflags}

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

rm -fv %{buildroot}%{zlib_multilibdir}/libz.a || :

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
  if [ -d .%{zlib_multilibdir} ]; then
    find .%{zlib_multilibdir} -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/zlib-files.list
%else
# Runtime: versioned shared libs, man pages
{
  if [ -d .%{zlib_multilibdir} ]; then
    find .%{zlib_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libz.so.*'
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/zlib-runtime.list

%if %{zlib_enable_devel}
# Development: headers, pkgconfig, unversioned .so symlink
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  if [ -d .%{zlib_multilibdir} ]; then
    find .%{zlib_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libz.so'
    if [ -d .%{zlib_multilibdir}/pkgconfig ]; then
      find .%{zlib_multilibdir}/pkgconfig -type f -o -type l
    fi
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/zlib-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/zlib-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/zlib-runtime.list
%defattr(-,root,root,-)

%if %{zlib_enable_devel}
%files devel -f %{_builddir}/zlib-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.3.1-1.m264
- Initial RPM packaging for zlib.
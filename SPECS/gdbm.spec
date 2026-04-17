%define gdbm_version 1.26

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global gdbm_multilibdir /usr/lib/i386-linux-gnu
%global gdbm_enable_devel 0
%else
%global gdbm_multilibdir /usr/lib/x86_64-linux-gnu
%global gdbm_enable_devel 1
%endif

Name:           gdbm
Version:        %{gdbm_version}
Release:        1.m264%{?dist}
Summary:        GNU Database Manager

%if "%{_target_cpu}" == "x86_64"
Provides:       libgdbm.so.6()(64bit)
Provides:       libgdbm_compat.so.4()(64bit)
%endif

License:        GPLv3+
URL:            https://www.gnu.org.ua/software/gdbm/
Source0:        https://ftp.gnu.org/gnu/gdbm/gdbm-%{version}.tar.gz

%description
The GDBM package contains the GNU Database Manager. It is a library of database
functions that uses extensible hashing and works like the standard UNIX dbm.

%prep
%setup -q -n gdbm-%{version}

%if %{gdbm_enable_devel}
%package devel
Summary:        Development files for gdbm
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers and the unversioned shared library symlinks for developing against GDBM.
%endif

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
    --libdir=%{gdbm_multilibdir} \
    --disable-static \
    --enable-libgdbm-compat \
    ${CONFIG_HOST}

make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

rm -f %{buildroot}/usr/share/info/dir || :

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/*.a || :
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/*.la || :
%else
rm -fv %{buildroot}/usr/lib/x86_64-linux-gnu/*.a || :
rm -fv %{buildroot}/usr/lib/x86_64-linux-gnu/*.la || :

mkdir -pv %{buildroot}/usr/lib
if [ -e %{buildroot}/usr/lib/x86_64-linux-gnu/libgdbm.so ]; then
  ln -sv x86_64-linux-gnu/libgdbm.so %{buildroot}/usr/lib/libgdbm.so || :
fi
if [ -e %{buildroot}/usr/lib/x86_64-linux-gnu/libgdbm_compat.so ]; then
  ln -sv x86_64-linux-gnu/libgdbm_compat.so %{buildroot}/usr/lib/libgdbm_compat.so || :
fi
%endif

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  find .%{gdbm_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/gdbm-files.list
%else
# Runtime: versioned shared libs, info pages, man pages
{
  find .%{gdbm_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so.*'
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -o -type l
  fi
  if [ -d ./usr/share/info ]; then
    find ./usr/share/info -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
  if [ -d ./usr/share/locale ]; then
    find ./usr/share/locale -type f -path './usr/share/locale/*/LC_MESSAGES/gdbm.mo'
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/gdbm-runtime.list

%if %{gdbm_enable_devel}
# Development: headers, unversioned .so symlinks
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{gdbm_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so' ! -name '*.so.*'
  if [ -f ./usr/lib/libgdbm.so ]; then
    echo ./usr/lib/libgdbm.so
  fi
  if [ -f ./usr/lib/libgdbm_compat.so ]; then
    echo ./usr/lib/libgdbm_compat.so
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/gdbm-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/gdbm-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/gdbm-runtime.list
%defattr(-,root,root,-)

%if %{gdbm_enable_devel}
%files devel -f %{_builddir}/gdbm-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.26-1.m264
- Initial RPM packaging for gdbm with multiarch layout.

%define expat_version 2.7.3

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global expat_multilibdir /usr/lib/i386-linux-gnu
%global expat_enable_devel 0
%else
%global expat_multilibdir /usr/lib/x86_64-linux-gnu
%global expat_enable_devel 1
%endif

Name:           expat
Version:        %{expat_version}
Release:        1.m264%{?dist}
Summary:        Stream-oriented XML parser library

%if "%{_target_cpu}" == "x86_64"
Provides:       libexpat.so.1()(64bit)
%endif

License:        MIT
URL:            https://libexpat.github.io/
Source0:        https://github.com/libexpat/libexpat/releases/download/R_%{version}/expat-%{version}.tar.xz

%if %{expat_enable_devel}
%package devel
Summary:        Development files for expat
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlink
for developing against expat.
%endif

%description
Expat is an XML parser library written in C.

%prep
%setup -q -n expat-%{version}

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
    --libdir=%{expat_multilibdir} \
    --disable-static \
    --docdir=%{_datadir}/doc/expat-%{version} \
    ${CONFIG_HOST}

make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

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
%endif

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  find .%{expat_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/expat-files.list
%else
# Runtime: versioned shared libs, binaries, man pages, docs
{
  find .%{expat_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so.*'
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
  if [ -d ./usr/share/doc ]; then
    find ./usr/share/doc -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/expat-runtime.list

%if %{expat_enable_devel}
# Development: headers, pkgconfig, cmake, unversioned .so symlink
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{expat_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so' ! -name '*.so.*'
  if [ -d .%{expat_multilibdir}/pkgconfig ]; then
    find .%{expat_multilibdir}/pkgconfig -type f -o -type l
  fi
  if [ -d .%{expat_multilibdir}/cmake ]; then
    find .%{expat_multilibdir}/cmake -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/expat-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/expat-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/expat-runtime.list
%defattr(-,root,root,-)

%if %{expat_enable_devel}
%files devel -f %{_builddir}/expat-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.7.3-1.m264
- Gen3 update: real -devel split, explicit Provides for libexpat.so.1, normalized filelists.

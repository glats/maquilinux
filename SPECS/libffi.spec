%define libffi_version 3.5.2

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global libffi_multilibdir /usr/lib/i386-linux-gnu
%global libffi_enable_devel 0
%else
%global libffi_multilibdir /usr/lib/x86_64-linux-gnu
%global libffi_enable_devel 1
%endif

Name:           libffi
Version:        %{libffi_version}
Release:        1.m264%{?dist}
Summary:        Foreign Function Interface library

%if "%{_target_cpu}" == "x86_64"
Provides:       libffi.so.8()(64bit)
%endif

License:        MIT
URL:            https://github.com/libffi/libffi
Source0:        https://github.com/libffi/libffi/releases/download/v%{version}/libffi-%{version}.tar.gz

%if %{libffi_enable_devel}
%package devel
Summary:        Development files for libffi
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlink
for developing against libffi.
%endif

%description
Libffi provides a portable, high-level programming interface to various calling
conventions. This allows programs to call any function specified at run time.

%prep
%setup -q -n libffi-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
CONFIG_HOST=--host=i686-pc-linux-gnu
CONFIG_GCC_ARCH=--with-gcc-arch=i686
%else
CONFIG_HOST=""
CONFIG_GCC_ARCH=--with-gcc-arch=native
%endif

./configure \
    --prefix=%{_prefix} \
    --libdir=%{libffi_multilibdir} \
    --disable-static \
    ${CONFIG_GCC_ARCH} \
    ${CONFIG_HOST}

make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

# Fix install paths if libffi installs to wrong location
%if "%{_target_cpu}" != "i686"
if [ -d "%{buildroot}/usr/lib64" ]; then
  mkdir -p "%{buildroot}%{libffi_multilibdir}"
  cp -a "%{buildroot}/usr/lib64/." "%{buildroot}%{libffi_multilibdir}/"
  rm -rf "%{buildroot}/usr/lib64"
fi
if [ -d "%{buildroot}/usr/lib/lib" ]; then
  mkdir -p "%{buildroot}%{libffi_multilibdir}"
  cp -a "%{buildroot}/usr/lib/lib/." "%{buildroot}%{libffi_multilibdir}/"
  rm -rf "%{buildroot}/usr/lib/lib"
fi
%else
# With /usr/lib32 symlink to /usr/lib/i386-linux-gnu, 32-bit libs automatically
# end up in the correct multiarch directory. No manual migration needed.
%endif

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_datadir} || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

# Remove static .la files
rm -f %{buildroot}%{libffi_multilibdir}/*.la || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
# For i686, files are in /usr/lib/lib32 (symlink to /usr/lib/i386-linux-gnu)
# and also in /usr/lib/i386-linux-gnu/pkgconfig (not under the symlink)
# List them from both paths so RPM sees them correctly
{
  find ./usr/lib/lib32 -type f -o -type l
  find ./usr/lib/i386-linux-gnu/pkgconfig -type f -o -type l 2>/dev/null || :
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libffi-files.list
%else
# Runtime: versioned shared libs, info pages
{
  find .%{libffi_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so.*'
  if [ -d ./usr/share/info ]; then
    find ./usr/share/info -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libffi-runtime.list

%if %{libffi_enable_devel}
# Development: headers, pkgconfig, unversioned .so symlink, man pages
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{libffi_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so' ! -name '*.so.*'
  if [ -d .%{libffi_multilibdir}/pkgconfig ]; then
    find .%{libffi_multilibdir}/pkgconfig -type f -o -type l
  fi
  if [ -d ./usr/share/man/man3 ]; then
    find ./usr/share/man/man3 -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libffi-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/libffi-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/libffi-runtime.list
%defattr(-,root,root,-)

%if %{libffi_enable_devel}
%files devel -f %{_builddir}/libffi-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 3.5.2-1.m264
- Initial packaging with multiarch support.

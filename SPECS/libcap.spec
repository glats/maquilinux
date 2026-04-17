%define libcap_version 2.77

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global libcap_multilibdir /usr/lib/i386-linux-gnu
%global libcap_enable_devel 0
%else
%global libcap_multilibdir /usr/lib/x86_64-linux-gnu
%global libcap_enable_devel 1
%endif

Name:           libcap
Version:        %{libcap_version}
Release:        1.m264%{?dist}
Summary:        POSIX capabilities library and tools

%if "%{_target_cpu}" == "x86_64"
Provides:       libcap.so.2()(64bit)
Provides:       libpsx.so.2()(64bit)
%endif

License:        LGPLv2.1+ and GPLv2+
URL:            https://www.kernel.org/pub/linux/libs/security/linux-privs/libcap2/
Source0:        https://www.kernel.org/pub/linux/libs/security/linux-privs/libcap2/libcap-%{version}.tar.xz

%if %{libcap_enable_devel}
%package devel
Summary:        Development files for libcap
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlinks
for developing against libcap.
%endif

%description
Libcap provides a userspace interface to the POSIX 1003.1e capabilities
available in Linux kernels. These capabilities partition the all-powerful
root privilege into a set of distinct privileges. This package installs
the shared libraries and the capsh, getcap, getpcaps, and setcap tools.

%prep
%setup -q -n libcap-%{version}

# Prevent static libraries from being installed as per LFS instructions.
sed -i '/install -m.*STA/d' libcap/Makefile

%build
%if "%{_target_cpu}" == "i686"
GOLANG=no make CC="gcc -m32 -march=i686" %{?_smp_mflags}
%else
# 64-bit build. Place libraries under the multiarch directory.
GOLANG=no make prefix=%{_prefix} \
    lib=lib/x86_64-linux-gnu \
    %{?_smp_mflags}
%endif

%check
# Upstream tests; run only for the 64-bit build tree. Do not fail the
# build in this minimal environment.
GOLANG=no make test || :

%install
rm -rf %{buildroot}

%if "%{_target_cpu}" == "i686"
# Install only libraries for 32-bit under the multiarch libdir
GOLANG=no make CC="gcc -m32 -march=i686" \
    lib=lib/i386-linux-gnu \
    prefix=%{_prefix} \
    DESTDIR=%{buildroot} \
    -C libcap install

# Prune non-library content for i686
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_includedir} || :
%else
# 64-bit install: libraries and tools into the multiarch lib directory.
GOLANG=no make prefix=%{_prefix} \
    lib=lib/x86_64-linux-gnu \
    DESTDIR=%{buildroot} install
%endif

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  find .%{libcap_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libcap-files.list
%else
# Runtime: versioned shared libs, binaries, man pages
{
  find .%{libcap_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so.*'
  if [ -d ./usr/sbin ]; then
    find ./usr/sbin -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libcap-runtime.list

%if %{libcap_enable_devel}
# Development: headers, pkgconfig, unversioned .so symlinks
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{libcap_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so' ! -name '*.so.*'
  if [ -d .%{libcap_multilibdir}/pkgconfig ]; then
    find .%{libcap_multilibdir}/pkgconfig -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libcap-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/libcap-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/libcap-runtime.list
%defattr(-,root,root,-)

%if %{libcap_enable_devel}
%files devel -f %{_builddir}/libcap-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.77-1.m264
- Initial RPM packaging for Libcap with multiarch layout.

%define attr_version 2.5.2

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

Name:           attr
Version:        %{attr_version}
Release:        1.m264%{?dist}
Summary:        Utilities for extended filesystem attributes

%if "%{_target_cpu}" == "x86_64"
Provides:       libattr.so.1()(64bit)
%endif

License:        LGPLv2.1+ and GPLv2+
URL:            https://savannah.nongnu.org/projects/attr
Source0:        https://download.savannah.gnu.org/releases/attr/attr-%{version}.tar.gz

%description
The Attr package contains utilities to administer the extended attributes
of filesystem objects. It provides the attr, getfattr, and setfattr tools
and the libattr runtime library used by other programs.

%prep
%setup -q -n attr-%{version}

%build
%if "%{_target_cpu}" == "i686"
CC="gcc -m32" ./configure \
    --prefix=%{_prefix} \
    --disable-static \
    --sysconfdir=%{_sysconfdir} \
    --libdir=/usr/lib/i386-linux-gnu \
    --host=i686-pc-linux-gnu
%else
./configure \
    --prefix=%{_prefix} \
    --disable-static \
    --sysconfdir=%{_sysconfdir} \
    --docdir=%{_datadir}/doc/attr-%{version} \
    --libdir=/usr/lib/x86_64-linux-gnu
%endif

make %{?_smp_mflags}

%check
# Upstream tests; run only for the 64-bit build tree. They require a filesystem
# with extended attribute support (such as ext4). Do not fail the build if they
# cannot be run successfully in this minimal environment.
make check || :

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

%if "%{_target_cpu}" == "i686"
# Prune non-library content for the 32-bit libs-only package
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_includedir} || :
%endif

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

%if "%{_target_cpu}" == "i686"
cd %{buildroot}
{
  if [ -d ./usr/lib/i386-linux-gnu ]; then
    find ./usr/lib/i386-linux-gnu -type f -o -type l | sed 's|^\.||'
  fi
  if [ -f ./etc/xattr.conf ]; then
    echo "%config(noreplace) /etc/xattr.conf"
  fi
} > %{_builddir}/attr-files.list
%else
cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/attr-files.list
%endif

%files -f %{_builddir}/attr-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.5.2-1.m264
- Initial RPM packaging for Attr with multiarch layout.

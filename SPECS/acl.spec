%define acl_version 2.3.2

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

Name:           acl
Version:        %{acl_version}
Release:        1.m264%{?dist}
Summary:        Access control list utilities

%if "%{_target_cpu}" == "x86_64"
Provides:       libacl.so.1()(64bit)
%endif

License:        LGPLv2.1+ and GPLv2+
URL:            https://savannah.nongnu.org/projects/acl
Source0:        https://download.savannah.gnu.org/releases/acl/acl-%{version}.tar.xz

%description
The Acl package contains utilities to administer POSIX Access Control Lists,
which provide fine-grained discretionary access rights for files and
directories. It provides the chacl, getfacl, and setfacl tools and the
libacl runtime library used by other programs.

%prep
%setup -q -n acl-%{version}

%build
%if "%{_target_cpu}" == "i686"
CC="gcc -m32" ./configure \
    --prefix=%{_prefix} \
    --disable-static \
    --libdir=/usr/lib/i386-linux-gnu \
    --host=i686-pc-linux-gnu
%else
./configure \
    --prefix=%{_prefix} \
    --disable-static \
    --docdir=%{_datadir}/doc/acl-%{version} \
    --libdir=/usr/lib/x86_64-linux-gnu
%endif

make %{?_smp_mflags}

%check
# Upstream tests require a filesystem with ACL support. One test (cp.test)
# is known to fail because Coreutils is not built with ACL support yet.
# Do not fail the build if the tests do not pass in this environment.
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
} > %{_builddir}/acl-files.list
%else
cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/acl-files.list
%endif

%files -f %{_builddir}/acl-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.3.2-1.m264
- Initial RPM packaging for Acl with multiarch layout.

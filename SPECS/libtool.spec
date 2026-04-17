Name:           libtool
Version:        2.5.4
Release:        1.m264%{?dist}
Summary:        Generic library support script

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        GPLv2+
URL:            https://www.gnu.org/software/libtool/
Source0:        libtool-%{version}.tar.xz

%description
GNU Libtool is a generic library support script. It hides the complexity of
using shared libraries behind a consistent, portable interface.

%prep
%setup -q -n libtool-%{version}

%build
%if "%{_target_cpu}" == "i686"
CC="gcc -m32" \
./configure \
    --host=i686-pc-linux-gnu \
    --prefix=%{_prefix} \
    --libdir=/usr/lib/i386-linux-gnu
%else
./configure \
    --prefix=%{_prefix} \
    --libdir=/usr/lib/x86_64-linux-gnu
%endif

make %{?_smp_mflags}

%check
# Upstream tests; do not fail the build in this minimal environment.
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

%if "%{_target_cpu}" == "i686"
# For the 32-bit build, ship only libraries under the multiarch libdir
# Remove binaries, docs and manpages so the i686 RPM is libs-only
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir}/info || :
rm -rf %{buildroot}%{_datadir}/aclocal || :
rm -rf %{buildroot}%{_datadir}/libtool || :
# Remove static library if present
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/libltdl.a || :
%else
# 64-bit: remove static library only used by tests (as per MLFS)
rm -fv %{buildroot}/usr/lib/x86_64-linux-gnu/libltdl.a || :
rm -fv %{buildroot}/usr/lib/libltdl.a || :
%endif

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

%if "%{_target_cpu}" == "i686"
# Files list for i686: only 32-bit library paths
cd %{buildroot}
{
  if [ -d ./usr/lib/i386-linux-gnu ]; then
    find ./usr/lib/i386-linux-gnu -type f -o -type l | sed 's|^\.||'
  fi
} > %{_builddir}/libtool-files.list
%else
# Files list for x86_64: include everything installed
cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/libtool-files.list
%endif

%files -f %{_builddir}/libtool-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.5.4-1.m264
- Initial RPM packaging for libtool with multiarch layout (64/32).

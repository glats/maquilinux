Name:           gettext
Version:        0.26
Release:        1.m264%{?dist}
Summary:        GNU internationalization utilities and libraries

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        GPLv3+ and LGPLv2+
URL:            https://www.gnu.org/software/gettext/
Source0:        gettext-%{version}.tar.xz

%description
The GNU gettext package provides a set of tools and libraries for internationalization
and localization (i18n), including message translation for applications.

%prep
%setup -q -n gettext-%{version}

%build
%if "%{_target_cpu}" == "i686"
CC="gcc -m32" CXX="g++ -m32" \
./configure \
    --prefix=%{_prefix} \
    --host=i686-pc-linux-gnu \
    --disable-static \
    --libdir=/usr/lib/i386-linux-gnu
%else
./configure \
    --prefix=%{_prefix} \
    --disable-static \
    --docdir=%{_datadir}/doc/gettext-%{version} \
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
# i686: ship only 32-bit libraries; remove bins, docs, man, includes, share
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/*.a || :
if [ -f %{buildroot}/usr/lib/i386-linux-gnu/preloadable_libintl.so ]; then
  chmod -v 0755 %{buildroot}/usr/lib/i386-linux-gnu/preloadable_libintl.so
fi
%else
# x86_64: prune static libs and fix mode for preloadable lib if present
rm -fv %{buildroot}/usr/lib/x86_64-linux-gnu/*.a || :
if [ -f %{buildroot}/usr/lib/x86_64-linux-gnu/preloadable_libintl.so ]; then
  chmod -v 0755 %{buildroot}/usr/lib/x86_64-linux-gnu/preloadable_libintl.so
fi
%endif

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

%if "%{_target_cpu}" == "i686"
cd %{buildroot}
{
  if [ -d ./usr/lib/i386-linux-gnu ]; then
    find ./usr/lib/i386-linux-gnu -type f -o -type l | sed 's|^\.||'
  fi
} > %{_builddir}/gettext-files.list
%else
cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/gettext-files.list
%endif

%files -f %{_builddir}/gettext-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 0.26-1.m264
- Initial RPM packaging for gettext with multiarch layout (64/32).

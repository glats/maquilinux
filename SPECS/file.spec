Name:           file
Version:        5.46
Release:        1.m264%{?dist}
Summary:        File type identification utility

# This spec is built in a minimal LFS-style chroot without the usual
# debuginfo and brp helper tools. Disable those automatic steps so
# rpmbuild does not try to call find-debuginfo or related scripts.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        BSD
URL:            https://astron.com/file/
Source0:        https://astron.com/pub/file/file-%{version}.tar.gz

%description
The File package contains the file(1) utility which is used to identify
file types. It uses "magic" number tests and other heuristics to classify
files, and provides the libmagic library used by other programs.

%prep
%setup -q -n file-%{version}

%build
%if "%{_target_cpu}" == "i686"
CC="gcc -m32" ./configure \
    --prefix=%{_prefix} \
    --libdir=/usr/lib/i386-linux-gnu \
    --host=i686-pc-linux-gnu
%else
./configure \
    --prefix=%{_prefix} \
    --libdir=/usr/lib/x86_64-linux-gnu
%endif

make %{?_smp_mflags}

%check
# Upstream tests; run only for the 64-bit build tree
make check || :

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

%if "%{_target_cpu}" == "i686"
# i686: libs-only
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_includedir} || :
%endif

%if "%{_target_cpu}" == "i686"
cd %{buildroot}
{
  if [ -d ./usr/lib/i386-linux-gnu ]; then
    find ./usr/lib/i386-linux-gnu -type f -o -type l | sed 's|^\.||'
  fi
} > %{_builddir}/file-files.list
%else
cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/file-files.list
%endif

%files -f %{_builddir}/file-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 5.46-1.m264
- Initial RPM packaging for file with multiarch layout.

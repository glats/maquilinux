Name:           bc
Version:        7.0.3
Release:        1.m264%{?dist}
Summary:        Arbitrary precision numeric processing language

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        BSD-2-Clause
URL:            https://git.gavinhoward.com/gavin/bc
Source0:        bc-%{version}.tar.xz

%description
The bc package provides the classic arbitrary precision calculator language
and the dc reverse-polish calculator.

%prep
%setup -q -n bc-%{version}

%build
# Follow MLFS: use gcc -std=c99 and configure with -G -O3 -r
CC="gcc -std=c99" ./configure \
    --prefix=%{_prefix} \
    -G -O3 -r

make %{?_smp_mflags}

%check
make test || :

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/bc-files.list

%files -f %{_builddir}/bc-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 7.0.3-1.m264
- Initial RPM packaging for bc following MLFS instructions.

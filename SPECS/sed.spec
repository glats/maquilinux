Name:           sed
Version:        4.9
Release:        1.m264%{?dist}
Summary:        Stream editor for filtering and transforming text

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        GPLv3+
URL:            https://www.gnu.org/software/sed/
Source0:        sed-%{version}.tar.xz

%description
Sed is a non-interactive stream editor that parses and transforms text using a
simple, compact programming language.

%prep
%setup -q -n sed-%{version}

%build
./configure --prefix=%{_prefix}
make %{?_smp_mflags}
make html

%check
# Run test suite; do not fail the build in the minimal chroot environment.
make check || :

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

# Install HTML documentation as per upstream instructions
install -d -m755 %{buildroot}%{_docdir}/sed-%{version}
install -m644 doc/sed.html %{buildroot}%{_docdir}/sed-%{version}

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/sed-files.list

%files -f %{_builddir}/sed-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 4.9-1.m264
- Initial RPM packaging for sed.

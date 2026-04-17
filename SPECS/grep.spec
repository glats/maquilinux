Name:           grep
Version:        3.12
Release:        1.m264%{?dist}
Summary:        Print lines matching a pattern

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        GPLv3+
URL:            https://www.gnu.org/software/grep/
Source0:        grep-%{version}.tar.xz

%description
Grep is a utility that searches through the contents of files looking for lines
that match a specified pattern.

%prep
%setup -q -n grep-%{version}

# Remove deprecation warning that breaks some package test suites (MLFS step)
sed -i "s/echo/#echo/" src/egrep.sh

%build
./configure --prefix=%{_prefix}
make %{?_smp_mflags}

%check
# Upstream tests; do not fail the build in the minimal chroot.
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/grep-files.list

%files -f %{_builddir}/grep-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 3.12-1.m264
- Initial RPM packaging for grep.

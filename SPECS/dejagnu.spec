Name:           dejagnu
Version:        1.6.3
Release:        1.m264%{?dist}
Summary:        Framework for testing other programs

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        GPLv3+
URL:            https://www.gnu.org/software/dejagnu/
Source0:        https://ftp.gnu.org/gnu/dejagnu/dejagnu-%{version}.tar.gz

%description
DejaGNU is a framework for running test suites on GNU tools and other
programs. It provides a front-end to Expect and Tcl for controlling and
testing other software.

%prep
%setup -q -n dejagnu-%{version}

%build
mkdir build
pushd build
../configure --prefix=%{_prefix}
makeinfo --html --no-split -o doc/dejagnu.html ../doc/dejagnu.texi
makeinfo --plaintext       -o doc/dejagnu.txt  ../doc/dejagnu.texi
popd

%check
pushd build
make check || :
popd

%install
rm -rf %{buildroot}
pushd build
make DESTDIR=%{buildroot} install
popd

install -vdm755 %{buildroot}%{_docdir}/dejagnu-%{version}
install -vm644 build/doc/dejagnu.{html,txt} %{buildroot}%{_docdir}/dejagnu-%{version}/

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/dejagnu-files.list

%files -f %{_builddir}/dejagnu-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.6.3-1.m264
- Initial RPM packaging for DejaGNU following MLFS instructions.

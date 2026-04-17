Name:           tcl
Version:        8.6.17
Release:        1.m264%{?dist}
Summary:        Tool Command Language interpreter and libraries

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        BSD
URL:            https://www.tcl.tk/
Source0:        https://prdownloads.sourceforge.net/tcl/tcl%{version}-src.tar.gz
Source1:        https://prdownloads.sourceforge.net/tcl/tcl%{version}-html.tar.gz

%description
Tcl (Tool Command Language) is a powerful yet easy to learn dynamic
programming language suitable for a wide range of uses, including web and
desktop applications, networking, administration, testing, and many more.
This package provides the Tcl interpreter and its development files.

%prep
%setup -q -n tcl%{version}

%build
pushd unix
SRCDIR=$(pwd -P)/..
./configure \
    --prefix=%{_prefix} \
    --mandir=%{_mandir} \
    --disable-rpath

make %{?_smp_mflags}

sed -e "s|$SRCDIR/unix|/usr/lib|" \
    -e "s|$SRCDIR|/usr/include|"  \
    -i tclConfig.sh

sed -e "s|$SRCDIR/unix/pkgs/tdbc1.1.12|/usr/lib/tdbc1.1.12|" \
    -e "s|$SRCDIR/pkgs/tdbc1.1.12/generic|/usr/include|"     \
    -e "s|$SRCDIR/pkgs/tdbc1.1.12/library|/usr/lib/tcl8.6|"  \
    -e "s|$SRCDIR/pkgs/tdbc1.1.12|/usr/include|"             \
    -i pkgs/tdbc1.1.12/tdbcConfig.sh

sed -e "s|$SRCDIR/unix/pkgs/itcl4.3.4|/usr/lib/itcl4.3.4|" \
    -e "s|$SRCDIR/pkgs/itcl4.3.4/generic|/usr/include|"    \
    -e "s|$SRCDIR/pkgs/itcl4.3.4|/usr/include|"            \
    -i pkgs/itcl4.3.4/itclConfig.sh
popd

%check
pushd unix
LC_ALL=C.UTF-8 make test || :
popd

%install
rm -rf %{buildroot}
pushd unix
make DESTDIR=%{buildroot} install
chmod 644 %{buildroot}/usr/lib/libtclstub8.6.a
chmod -v u+w %{buildroot}/usr/lib/libtcl8.6.so
make DESTDIR=%{buildroot} install-private-headers
popd

ln -sfv tclsh8.6 %{buildroot}/usr/bin/tclsh
mv -v %{buildroot}/usr/share/man/man3/Thread.3 %{buildroot}/usr/share/man/man3/Tcl_Thread.3

# Install optional HTML documentation
mkdir -pv %{buildroot}%{_docdir}/tcl-%{version}
tar -xf %{SOURCE1} --strip-components=1 -C %{buildroot}%{_docdir}/tcl-%{version}

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/tcl-files.list

%files -f %{_builddir}/tcl-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 8.6.17-1.m264
- Initial RPM packaging for Tcl following MLFS instructions.

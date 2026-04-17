Name:           bison
Version:        3.8.2
Release:        1.m264%{?dist}
Summary:        GNU parser generator

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        GPLv3+
URL:            https://www.gnu.org/software/bison/
Source0:        bison-%{version}.tar.xz

%description
Bison is a general-purpose parser generator that converts a grammar
specification for an LALR(1) context-free grammar into a C program to parse
that grammar. It is a replacement for Yacc.

%prep
%setup -q -n bison-%{version}

%build
./configure \
    --prefix=%{_prefix} \
    --docdir=%{_datadir}/doc/bison-%{version}

make %{?_smp_mflags}

%check
# Upstream test suite; do not fail the build in this minimal chroot.
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/bison-files.list

%files -f %{_builddir}/bison-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 3.8.2-1.m264
- Initial RPM packaging for bison.

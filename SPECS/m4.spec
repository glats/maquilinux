Name:           m4
Version:        1.4.20
Release:        1.m264%{?dist}
Summary:        GNU macro processor

# This spec is built in a minimal LFS-style chroot without the usual
# debuginfo and brp helper tools. Disable those automatic steps so
# rpmbuild does not try to call find-debuginfo or related scripts.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        GPLv3+
URL:            https://www.gnu.org/software/m4/
Source0:        m4-%{version}.tar.xz

%description
The GNU m4 package contains a macro processor. The m4 program copies the
given files while expanding the macros that they contain. These macros
are either built-in or user-defined and can take any number of arguments.
Besides performing macro expansion, m4 has built-in functions for
including named files, running Unix commands, performing integer
arithmetic, manipulating text, recursion, and more. It can be used as a
front end to a compiler or as a standalone macro processor.

%prep
%setup -q -n m4-%{version}

%build
# 64-bit build only, as in the MLFS instructions
./configure \
    --prefix=%{_prefix}

make %{?_smp_mflags}

%check
# Upstream test suite; allow failures not to break the build in bootstrap
make check || :

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/m4-files.list

%files -f %{_builddir}/m4-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.4.20-1.m264
- Initial RPM packaging for m4 following MLFS instructions.

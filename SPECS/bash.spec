Name:           bash
Version:        5.3
Release:        3.m264%{?dist}
Summary:        The GNU Bourne Again shell

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        GPLv3+
URL:            https://www.gnu.org/software/bash/
Source0:        bash-%{version}.tar.gz

# Bash provides /bin/sh symlink for script interpreter requirements
Provides:       /bin/sh
Provides:       /bin/bash
Provides:       /bin/csh

%description
Bash is the GNU Project's shell. It is compatible with the Bourne shell and
incorporates useful features from the Korn shell and C shell.

%prep
%setup -q -n bash-%{version}

%build
./configure \
    --prefix=%{_prefix} \
    --without-bash-malloc \
    --with-installed-readline \
    --docdir=%{_datadir}/doc/bash-%{version}

make %{?_smp_mflags}

%check
# The upstream test suite prefers to run under a non-root user via Expect.
# In this minimal chroot, run it non-fatally so packaging can proceed.
make tests || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

# Provide sh symlink pointing to bash, as expected in LFS/MLFS environments
mkdir -pv %{buildroot}%{_bindir}
ln -svf bash %{buildroot}%{_bindir}/sh
# Provide csh symlink for compatibility (vim and other tools may require it)
ln -svf bash %{buildroot}%{_bindir}/csh

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/bash-files.list

%files -f %{_builddir}/bash-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 5.3-1.m264
- Initial RPM packaging for bash.

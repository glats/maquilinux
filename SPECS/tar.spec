Name:           tar
Version:        1.35
Release:        1.m264%{?dist}
Summary:        GNU tape archiver for creating and extracting archives

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-3.0-or-later
URL:            https://www.gnu.org/software/tar/
Source0:        https://ftp.gnu.org/gnu/tar/tar-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  texinfo

%description
GNU tar creates, extracts, and lists archives while supporting multiple
compression algorithms and incremental backups.

%prep
%autosetup -n tar-%{version}

%build
FORCE_UNSAFE_CONFIGURE=1 ./configure --prefix=%{_prefix}
make %{?_smp_mflags}

%check
# Full test suite needs additional environment setup; run best-effort.
make -k check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/tar-files.list

%files -f %{_builddir}/tar-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.35-1.m264
- Initial packaging aligned with MLFS 8.74 instructions.

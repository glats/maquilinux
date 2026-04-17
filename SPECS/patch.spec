Name:           patch
Version:        2.8
Release:        1.m264%{?dist}
Summary:        Apply changes to files using diff patches

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-2.0-or-later
URL:            https://www.gnu.org/software/patch/
Source0:        https://ftp.gnu.org/gnu/patch/patch-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  texinfo

%description
GNU Patch takes a patch file containing differences between original and
modified files and applies them to the originals.

%prep
%autosetup -n patch-%{version}

%build
./configure --prefix=%{_prefix}
make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
make DESTDIR=%{buildroot} install

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . \( -type f -o -type l \) -printf '/%%P\n' > %{builddir}/patch-files.list
test -s %{builddir}/patch-files.list

%files -f %{builddir}/patch-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.8-1.m264
- Initial packaging aligned with MLFS 8.73 instructions.

Name:           grub
Version:        2.12
Release:        1.m264%{?dist}
Summary:        The GNU GRand Unified Bootloader

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-3.0-or-later
URL:            https://www.gnu.org/software/grub/
Source0:        https://ftp.gnu.org/gnu/grub/grub-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  flex
BuildRequires:  bison
BuildRequires:  gettext

%description
GRUB is the GNU bootloader capable of loading a wide variety of operating
systems and kernels.

%prep
%autosetup -n grub-%{version}
echo depends bli part_gpt > grub-core/extra_deps.lst

%build
unset CFLAGS CPPFLAGS CXXFLAGS LDFLAGS
./configure \
    --prefix=%{_prefix} \
    --sysconfdir=%{_sysconfdir} \
    --disable-efiemu \
    --disable-werror
make %{?_smp_mflags}

%check
# Upstream does not recommend running tests in this environment.
:

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install
if [ -f %{buildroot}/etc/bash_completion.d/grub ]; then
  install -d %{buildroot}/usr/share/bash-completion/completions
  mv -f %{buildroot}/etc/bash_completion.d/grub \
        %{buildroot}/usr/share/bash-completion/completions/
fi

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/grub-files.list

%files -f %{_builddir}/grub-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.12-1.m264
- Initial packaging aligned with MLFS 8.67 instructions.

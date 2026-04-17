Name:           iproute2
Version:        6.17.0
Release:        1.m264%{?dist}
Summary:        Utilities for managing network interfaces and routing

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-2.0-or-later
URL:            https://wiki.linuxfoundation.org/networking/iproute2
Source0:        https://www.kernel.org/pub/linux/utils/net/iproute2/iproute2-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  bison
BuildRequires:  flex

%description
The iproute2 package provides the ip command suite plus assorted networking
utilities, replacing older net-tools programs.

%prep
%autosetup -n iproute2-%{version}
sed -i /ARPD/d Makefile
rm -fv man/man8/arpd.8

%build
make %{?_smp_mflags} NETNS_RUN_DIR=/run/netns

%check
# Upstream does not ship a working test suite for this environment.
:

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
make DESTDIR=%{buildroot} SBINDIR=%{_sbindir} install
install -Dm644 COPYING %{buildroot}/usr/share/doc/iproute2-%{version}/COPYING
for f in README*; do
  if [ -f "$f" ]; then
    install -Dm644 "$f" %{buildroot}/usr/share/doc/iproute2-%{version}/"$f"
  fi
done

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . \( -type f -o -type l \) -printf '/%%P\n' > %{builddir}/iproute2-files.list
test -s %{builddir}/iproute2-files.list

%files -f %{builddir}/iproute2-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 6.18.0-1.m264
- Initial packaging aligned with MLFS 8.69 instructions.

# SPECS/dhcpcd.spec
%define debug_package %{nil}

Name:           dhcpcd
Version:        10.0.6
Release:        1.m264%{?dist}
Summary:        DHCP client daemon
License:        BSD-2-Clause
URL:            https://github.com/NetworkConfiguration/dhcpcd
Source0:        https://github.com/NetworkConfiguration/dhcpcd/releases/download/v%{version}/dhcpcd-%{version}.tar.xz
Obsoletes:      dhcpcd < 10.0.6-2
BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  openssl-devel
BuildRequires: udev
Requires:       openrc

%description
dhcpcd is a POSIX compliant DHCP client that implements the DHCP client
part of the interaction between a host and a network. It is the daemon
used on Maqui Linux for dynamic IP address configuration on network interfaces.

%prep
%autosetup -p1

%build
# dhcpcd uses a custom configure script (NOT autoconf), so we call
# ./configure directly instead of the %configure macro.
./configure \
    --prefix=/usr \
    --sysconfdir=/etc \
    --localstatedir=/var/lib/dhcpcd \
    --privsepuser=dhcpcd \
    --dbdir=/var/lib/dhcpcd \
    --runstatedir=/run
%make_build

%install
%make_install

%pre
getent passwd dhcpcd >/dev/null || useradd -r -s /usr/sbin/nologin dhcpcd

%files
%attr(0755, root, root) %dir /var/lib/dhcpcd
%config(noreplace) /etc/conf.d/dhcpcd
%config(noreplace) /etc/dhcpcd.conf
/etc/init.d/dhcpcd
/usr/lib/dhcpcd/
/usr/sbin/dhcpcd
/usr/share/dhcpcd/hooks/
%attr(0755, root, root) %dir /usr/share/doc/dhcpcd-%{version}
%attr(0755, root, root) %dir /usr/share/licenses/dhcpcd-%{version}
/usr/share/man/man5/dhcpcd.conf.5.gz
/usr/share/man/man8/dhcpcd-run-hooks.8.gz
/usr/share/man/man8/dhcpcd.8.gz

%changelog
* Mon May 04 2026 Maqui Linux <info@maquilinux.org> - 10.0.6-1.m264
- Initial Maqui Linux release with m264 tag
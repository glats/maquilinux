Name:           sysklogd
Version:        2.7.2
Release:        1.m264%{?dist}
Summary:        System logging daemons (syslogd/klogd)

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        BSD and GPL-2.0-or-later
URL:            https://github.com/troglobit/sysklogd
Source0:        https://github.com/troglobit/sysklogd/releases/download/v%{version}/sysklogd-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  pkgconf
BuildRequires:  libcap

%description
Sysklogd provides the traditional syslogd and klogd daemons used to collect
and route kernel and userspace log messages on Unix systems.

%prep
%autosetup -n sysklogd-%{version}

%build
./configure --prefix=%{_prefix} \
            --sysconfdir=%{_sysconfdir} \
            --runstatedir=/run \
            --without-logger \
            --disable-static \
            --docdir=%{_datadir}/doc/sysklogd-%{version}
make %{?_smp_mflags}

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

install -d %{buildroot}/var/log
install -d %{buildroot}%{_sysconfdir}
cat > %{buildroot}/etc/syslog.conf <<'EOF'
# Begin /etc/syslog.conf

auth,authpriv.* -/var/log/auth.log
*.*;auth,authpriv.none -/var/log/sys.log
daemon.* -/var/log/daemon.log
kern.* -/var/log/kern.log
mail.* -/var/log/mail.log
user.* -/var/log/user.log
*.emerg *

# Do not open any internet ports.
secure_mode 2

# End /etc/syslog.conf
EOF

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/sysklogd-files.list

%files -f %{_builddir}/sysklogd-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.7.2-1.m264
- Initial packaging aligned with MLFS 8.84 instructions (syslog.conf secure defaults).

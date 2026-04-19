Name:           which
Version:        2.23
Release:        2.m264%{?dist}
Summary:        Shows the full path of shell commands

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-3.0-or-later
URL:            https://www.gnu.org/software/which/
# Download URL: https://ftp.gnu.org/gnu/which/which-%{version}.tar.gz
Source0:        which-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make

%description
GNU which takes one or more arguments. For each of its arguments it prints
to stdout the full path of the executables that would have been executed
when this argument had been entered at the shell prompt.

%prep
%setup -q -n which-%{version}

%build
%configure
make %{?_smp_mflags}

%install
make DESTDIR=%{buildroot} install

# Remove info dir file
rm -f %{buildroot}%{_infodir}/dir

%files
%defattr(-,root,root)
%{_bindir}/which
%{_mandir}/man1/which.1*
%{_infodir}/which.info*

%changelog
* Sat Apr 11 2026 Maqui Linux Team <team@maqui-linux.org> - 2.23-1.m264
- Initial packaging for Maqui Linux

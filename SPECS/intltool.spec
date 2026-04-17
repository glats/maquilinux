Name:           intltool
Version:        0.51.0
Release:        1.m264%{?dist}
Summary:        Tools for extracting translatable strings

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPLv2+
URL:            https://freedesktop.org/wiki/Software/intltool/
Source0:        https://launchpad.net/intltool/trunk/%{version}/+download/intltool-%{version}.tar.gz

BuildRequires:  perl

%description
Intltool is a set of tools for extracting translatable strings from source
files so that they can be translated using standard gettext utilities.

%prep
%setup -q -n intltool-%{version}

# Fix perl 5.22+ warning per MLFS instructions
sed -i 's:\\${:\\\${:' intltool-update.in

%build
./configure --prefix=%{_prefix}
make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install
install -D -m 0644 doc/I18N-HOWTO \
    %{buildroot}%{_datadir}/doc/intltool-%{version}/I18N-HOWTO
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/intltool-files.list

%files -f %{_builddir}/intltool-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 0.51.0-1.m264
- Initial packaging aligned with MLFS 8.47 instructions.

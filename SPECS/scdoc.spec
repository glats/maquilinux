Name:           scdoc
Version:        1.11.4
Release:        1.m264%{?dist}
Summary:        Small man page generator for POSIX systems

ExclusiveArch:  x86_64

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        MIT
URL:            https://sr.ht/~sircmpwn/scdoc/
Source0:        https://git.sr.ht/~sircmpwn/scdoc/archive/scdoc-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make

%description
scdoc is a small man page generator used by projects that write manual pages
in an scdoc-specific markup language.

%prep
%setup -q -n scdoc-%{version}

%build
make %{?_smp_mflags} PREFIX=%{_prefix}

%check
:

%install
rm -rf %{buildroot}
make PREFIX=%{_prefix} DESTDIR=%{buildroot} install

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/scdoc-files.list

%files -f %{_builddir}/scdoc-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.11.4-1.m264
- Initial packaging for RPM dependency.

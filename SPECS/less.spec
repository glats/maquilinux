Name:           less
Version:        685
Release:        1.m264%{?dist}
Summary:        A text file pager

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPLv3+
URL:            https://www.greenwoodsoftware.com/less/
Source0:        https://www.greenwoodsoftware.com/less/less-%{version}.tar.gz

%description
Less is a pager program similar to more, but with the ability to move
backward in the file as well as forward. It also does not have to read the
entire input file before starting, so it starts up more quickly than text
editors like vi.

%prep
%setup -q -n less-%{version}

%build
./configure \
    --prefix=%{_prefix} \
    --sysconfdir=%{_sysconfdir}

make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/less-files.list

%files -f %{_builddir}/less-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 685-1.m264
- Initial packaging of Less following MLFS 8.44 instructions.

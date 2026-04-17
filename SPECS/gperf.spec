Name:           gperf
Version:        3.3
Release:        1.m264%{?dist}
Summary:        A perfect hash function generator

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

License:        GPLv3+
URL:            https://www.gnu.org/software/gperf/
Source0:        https://ftp.gnu.org/gnu/gperf/gperf-%{version}.tar.gz

%description
Gperf generates perfect hash functions from a set of keywords.

%prep
%setup -q -n gperf-%{version}

%build
./configure \
    --prefix=%{_prefix} \
    --docdir=%{_datadir}/doc/gperf-%{version}

make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/gperf-files.list

%files -f %{_builddir}/gperf-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 3.3-1.m264
- Initial RPM packaging for gperf.

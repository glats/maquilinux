%define blddir	tzdata%{version}
Name:           tzdata
Version:        2025b
Release:        1.m264%{?dist}
Summary:        Time Zone Database
BuildArch:      noarch

# Built inside a minimal LFS-style chroot without find-debuginfo or brp helpers.
# Disable automatic debuginfo and BRP post scripts for consistent packaging.
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}
License:        Public Domain
URL:            https://www.iana.org/time-zones
Source0:        https://www.iana.org/time-zones/repository/releases/tzdata%{version}.tar.gz

%description
Sources for time zone and daylight saving time data
%prep
%setup -q -c -n %{blddir}
%build
%install

ZONEINFO=%{buildroot}/usr/share/zoneinfo
install -vdm 755 $ZONEINFO/{posix,right}

for tz in etcetera southamerica northamerica europe africa antarctica \
          asia australasia backward; do
    zic -L /dev/null   -d $ZONEINFO       ${tz}
    zic -L /dev/null   -d $ZONEINFO/posix ${tz}
    zic -L leapseconds -d $ZONEINFO/right ${tz}
done

cp -v zone.tab zone1970.tab iso3166.tab $ZONEINFO
zic -d $ZONEINFO -p America/New_York
unset ZONEINFO tz
install -vdm 755 %{buildroot}/etc
ln -sf /usr/share/zoneinfo/America/New_York %{buildroot}/etc/localtime

install -D -m644 LICENSE %{buildroot}/usr/share/licenses/%{name}/LICENSE

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/tzdata-files.list

%files -f %{_builddir}/tzdata-files.list
	%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2025b-1.m264
- Initial RPM packaging for LFS.
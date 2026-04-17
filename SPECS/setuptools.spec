Name:           setuptools
Version:        80.9.0
Release:        1.m264%{?dist}
Summary:        Build and installation utilities for Python packages

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

%global _enable_debug_package 0
%global _enable_debug_packages 0
%global _debugsource_packages %{nil}

License:        MIT
URL:            https://github.com/pypa/setuptools
Source0:        https://files.pythonhosted.org/packages/source/s/setuptools/setuptools-%{version}.tar.gz

BuildRequires:  python3
BuildArch:      noarch

%description
Setuptools provides the Python packaging build backend and helper commands
used to build, install, upgrade, and remove Python modules as wheels or
legacy eggs.

%prep
%setup -q -n setuptools-%{version}

%build
python3 -m pip wheel -w dist \
    --no-cache-dir \
    --no-build-isolation \
    --no-deps \
    $PWD

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
python3 -m pip install \
    --no-index \
    --find-links dist \
    --no-cache-dir \
    --no-build-isolation \
    --ignore-installed \
    --no-deps \
    --root %{buildroot} \
    --prefix %{_prefix} \
    setuptools

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . \( -type f -o -type l \) -printf '/%%P\n' | \
  awk '{ if ($0 ~ /[[:space:]]/) { gsub(/"/, "\\\"", $0); print "\"" $0 "\"" } else { print $0 } }' \
  > %{builddir}/setuptools-files.list
test -s %{builddir}/setuptools-files.list

%files -f %{builddir}/setuptools-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 80.9.0-1.m264
- Initial packaging aligned with MLFS 8.58 instructions.

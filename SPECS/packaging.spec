Name:           packaging
Version:        25.0
Release:        1.m264%{?dist}
Summary:        Core utilities for Python packaging interoperability

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        Apache-2.0 or BSD
URL:            https://github.com/pypa/packaging
Source0:        https://files.pythonhosted.org/packages/source/p/packaging/packaging-%{version}.tar.gz

BuildRequires:  python3

%description
The packaging module provides standardized implementations of version and
requirement handling for Python packages, as described by various PEPs.

%prep
%setup -q -n packaging-%{version}

%build
python3 -m pip wheel -w dist \
    --no-cache-dir \
    --no-build-isolation \
    --no-deps \
    $PWD

%install
rm -rf %{buildroot}
python3 -m pip install \
    --no-index \
    --find-links dist \
    --no-cache-dir \
    --no-build-isolation \
    --no-deps \
    --root %{buildroot} \
    --prefix %{_prefix} \
    packaging

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/packaging-files.list

%files -f %{_builddir}/packaging-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 25.0-1.m264
- Initial packaging aligned with MLFS 8.56 instructions.

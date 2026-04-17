Name:           wheel
Version:        0.46.1
Release:        1.m264%{?dist}
Summary:        Reference implementation of the Python wheel packaging format

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        MIT
URL:            https://github.com/pypa/wheel
Source0:        https://files.pythonhosted.org/packages/source/w/wheel/wheel-%{version}.tar.gz

BuildRequires:  python3

%description
Wheel provides the reference implementation of the wheel packaging
standard, including the command line utility for building and inspecting
wheel archives.

%prep
%setup -q -n wheel-%{version}

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
    wheel

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/wheel-files.list

%files -f %{_builddir}/wheel-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 0.46.1-1.m264
- Initial packaging aligned with MLFS 8.57 instructions.

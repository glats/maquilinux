Name:           flit-core
Version:        3.12.0
Release:        1.m264%{?dist}
Summary:        Build backend (core) for the Flit Python packaging tool

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        BSD
URL:            https://github.com/pypa/flit
Source0:        https://files.pythonhosted.org/packages/source/f/flit-core/flit_core-%{version}.tar.gz

BuildRequires:  python3

%description
Flit-core provides the PEP 517 build backend components of Flit, used for
building Python distribution archives for simple projects.

%prep
%setup -q -n flit_core-%{version}

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
    flit_core

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/flit-core-files.list

%files -f %{_builddir}/flit-core-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 3.12.0-1.m264
- Initial packaging aligned with MLFS 8.55 instructions.

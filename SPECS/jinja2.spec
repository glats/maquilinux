Name:           jinja2
Version:        3.1.6
Release:        1.m264%{?dist}
Summary:        Modern and designer-friendly templating engine for Python

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        BSD
URL:            https://palletsprojects.com/p/jinja/
Source0:        https://pypi.org/packages/source/J/Jinja2/jinja2-%{version}.tar.gz

BuildRequires:  python3

%description
Jinja2 is a fully featured template engine for Python, designed to be flexible
and fast with sandboxed execution and auto-escaping.

%prep
%setup -q -n jinja2-%{version}

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
    Jinja2

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/jinja2-files.list

%files -f %{_builddir}/jinja2-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 3.1.6-1.m264
- Initial packaging aligned with MLFS 8.78 instructions.

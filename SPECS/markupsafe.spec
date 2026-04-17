Name:           markupsafe
Version:        3.0.3
Release:        1.m264%{?dist}
Summary:        Safely implement XML/HTML markup in Python strings

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        BSD
URL:            https://palletsprojects.com/p/markupsafe/
Source0:        https://pypi.org/packages/source/M/MarkupSafe/markupsafe-%{version}.tar.gz

BuildRequires:  python3

%description
MarkupSafe is a small library for safe HTML and XML string handling, used by
Jinja2 and other templating systems.

%prep
%setup -q -n markupsafe-%{version}

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
    --no-deps \
    --root %{buildroot} \
    --prefix %{_prefix} \
    MarkupSafe

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . \( -type f -o -type l \) -printf '/%%P\n' > %{builddir}/markupsafe-files.list
test -s %{builddir}/markupsafe-files.list

%files -f %{builddir}/markupsafe-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 3.0.3-1.m264
- Initial packaging aligned with MLFS 8.77 instructions.

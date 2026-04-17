Name:           meson
Version:        1.9.1
Release:        1.m264%{?dist}
Summary:        High-productivity build system

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        Apache-2.0
URL:            https://mesonbuild.com
Source0:        https://files.pythonhosted.org/packages/source/m/meson/meson-%{version}.tar.gz

BuildRequires:  python3
BuildArch:      noarch

%description
Meson is an open source build system designed to be fast and easy to use,
with support for many languages and toolchains.

%prep
%setup -q -n meson-%{version}

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
    meson

install -Dm644 data/shell-completions/bash/meson \
    %{buildroot}/usr/share/bash-completion/completions/meson
install -Dm644 data/shell-completions/zsh/_meson \
    %{buildroot}/usr/share/zsh/site-functions/_meson

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . \( -type f -o -type l \) -printf '/%%P\n' | \
  awk '{ if ($0 ~ /[[:space:]]/) { gsub(/"/, "\\\"", $0); print "\"" $0 "\"" } else { print $0 } }' \
  > %{builddir}/meson-files.list
test -s %{builddir}/meson-files.list

%files -f %{builddir}/meson-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.10.0-1.m264
- Initial packaging aligned with MLFS 8.60 instructions.

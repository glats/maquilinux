Name:           openrc
Version:        0.63
Release:        1.m264%{?dist}
Summary:        The OpenRC init system

ExclusiveArch:  x86_64

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        BSD-2-Clause
URL:            https://github.com/OpenRC/openrc
Source0:        https://github.com/OpenRC/openrc/archive/refs/tags/openrc-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  meson
BuildRequires:  ninja
BuildRequires:  pkgconf
BuildRequires:  libcap

%description
OpenRC is a dependency-based init system.

%prep
%setup -q -n openrc-%{version}

%build
rm -rf build
meson setup build \
    --prefix=%{_prefix} \
    --sysconfdir=%{_sysconfdir} \
    --localstatedir=/var \
    --bindir=bin \
    --sbindir=sbin \
    --libdir=lib/x86_64-linux-gnu \
    --wrap-mode nodownload \
    --buildtype=release \
    -Daudit=disabled \
    -Dselinux=disabled \
    -Dpam=false \
    -Dbranding='"Maquilinux"' \
    -Dnewnet=true \
    -Dsysvinit=true \
    '-Dagetty=["tty1","tty2","tty3","tty4","tty5","tty6","ttyS0"]'

ninja -C build

%check
:

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}

DESTDIR=%{buildroot} ninja -C build install

if [ -e %{buildroot}%{_sbindir}/openrc-init ]; then
  ln -snf openrc-init %{buildroot}%{_sbindir}/init
fi

find %{buildroot} -type l -print | while IFS= read -r link; do \
  target="$(readlink "$link" 2>/dev/null || true)"; \
  case "$target" in \
    /*) \
      br_target="%{buildroot}${target}"; \
      if [ -e "$br_target" ] || [ -L "$br_target" ]; then \
        link_dir="$(dirname "$link")"; \
        rel_target="$(realpath --relative-to="$link_dir" "$br_target")"; \
        ln -snf "$rel_target" "$link"; \
      fi \
      ;; \
  esac; \
done

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . \( -type f -o -type l \) -printf '/%%P\n' | \
  while IFS= read -r p; do \
    case "$p" in \
      *[[:space:]]*) printf '"%%s"\n' "$p" ;; \
      *)             printf '%%s\n' "$p" ;; \
    esac; \
  done > %{builddir}/openrc-files.list

test -s %{builddir}/openrc-files.list

%files -f %{builddir}/openrc-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 0.63-1.m264
- Initial packaging of OpenRC for Maquilinux.

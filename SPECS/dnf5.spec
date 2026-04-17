Name:           dnf5
Version:        5.3.0.0
Release:        1.m264%{?dist}
Summary:        Command-line package manager (DNF5)

ExclusiveArch:  x86_64

%bcond_without perl5
%bcond_without python3

%if %{with perl5}
%global dnf5_with_perl5 ON
%else
%global dnf5_with_perl5 OFF
%endif

%if %{with python3}
%global dnf5_with_python3 ON
%else
%global dnf5_with_python3 OFF
%endif

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-2.0-or-later
URL:            https://github.com/rpm-software-management/dnf5
Source0:        %{url}/archive/%{version}/dnf5-%{version}.tar.gz

Requires:       libdnf5%{?_isa} = %{version}-%{release}
Requires:       libdnf5-cli%{?_isa} = %{version}-%{release}

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  cmake
BuildRequires:  pkgconf
BuildRequires:  gettext
BuildRequires:  zlib
BuildRequires:  sqlite
BuildRequires:  rpmdnf
BuildRequires:  libxml2-devel
BuildRequires:  glib2-devel
BuildRequires:  libffi

# DNF5 core dependencies
BuildRequires:  fmt-devel
BuildRequires:  json-c-devel
BuildRequires:  libsolv-devel
BuildRequires:  librepo-devel

# Used by libdnf5 configuration and state
BuildRequires:  toml11

%if %{with perl5} || %{with python3}
BuildRequires:  swig
%endif

%if %{with perl5}
BuildRequires:  perl
BuildRequires:  perl-devel
%endif

%if %{with python3}
BuildRequires:  python3
BuildRequires:  python3-devel
%endif

%description
DNF5 is a command-line package manager that automates the process of installing,
upgrading, configuring, and removing software in a consistent manner. It is the
next-generation version of DNF.

%package -n libdnf5
Summary:        Package management library for DNF5
Provides:       libdnf5.so.2()(64bit)

Requires:       libsolv
Requires:       librepo
Requires:       sqlite
Requires:       rpm

%description -n libdnf5
Package management library for DNF5.

%package -n libdnf5-cli
Summary:        Terminal/CLI helper library for DNF5
Provides:       libdnf5-cli.so.2()(64bit)

Requires:       libdnf5%{?_isa} = %{version}-%{release}

%description -n libdnf5-cli
Terminal helper library for DNF5.

%package -n libdnf5-devel
Summary:        Development files for libdnf5

Requires:       libdnf5%{?_isa} = %{version}-%{release}

%description -n libdnf5-devel
Development files for libdnf5.

%package -n libdnf5-cli-devel
Summary:        Development files for libdnf5-cli

Requires:       libdnf5-cli%{?_isa} = %{version}-%{release}
Requires:       libdnf5-devel%{?_isa} = %{version}-%{release}

%description -n libdnf5-cli-devel
Development files for libdnf5-cli.

%if %{with python3}
%package -n python3-libdnf5
Summary:        Python 3 bindings for libdnf5

Requires:       python3
Requires:       libdnf5%{?_isa} = %{version}-%{release}

%description -n python3-libdnf5
Python 3 bindings for libdnf5.
%endif

%if %{with perl5}
%package -n perl-libdnf5
Summary:        Perl bindings for libdnf5

Requires:       perl
Requires:       libdnf5%{?_isa} = %{version}-%{release}

%description -n perl-libdnf5
Perl bindings for libdnf5.
%endif

%prep
%setup -q -n dnf5-%{version}

%build
rm -rf _build
mkdir -p _build
pushd _build

export PKG_CONFIG_LIBDIR="/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig"
export CPPFLAGS="${CPPFLAGS:-} -I/usr/include/libxml2"
export CFLAGS="${CFLAGS:-} -I/usr/include/libxml2"
export CXXFLAGS="${CXXFLAGS:-} -I/usr/include/libxml2"
export LDFLAGS="${LDFLAGS:-} -L/usr/lib/x86_64-linux-gnu -Wl,-rpath-link,/usr/lib/x86_64-linux-gnu"

cmake .. \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_LIBDIR=lib/x86_64-linux-gnu \
    -DCMAKE_INSTALL_SYSCONFDIR=%{_sysconfdir} \
    -DCMAKE_INSTALL_LOCALSTATEDIR=/var \
    -DPACKAGE_VERSION=%{version} \
    -DWITH_SYSTEMD=OFF \
    -DWITH_DNF5DAEMON_CLIENT=OFF \
    -DWITH_DNF5DAEMON_SERVER=OFF \
    -DWITH_DNF5_PLUGINS=OFF \
    -DWITH_PLUGIN_ACTIONS=OFF \
    -DWITH_PLUGIN_APPSTREAM=OFF \
    -DWITH_PLUGIN_EXPIRED_PGP_KEYS=OFF \
    -DWITH_PLUGIN_RHSM=OFF \
    -DWITH_PLUGIN_MANIFEST=OFF \
    -DWITH_PYTHON_PLUGINS_LOADER=OFF \
    -DWITH_ACL=OFF \
    -DWITH_COMPS=OFF \
    -DWITH_MODULEMD=OFF \
    -DWITH_HTML=OFF \
    -DWITH_MAN=OFF \
    -DWITH_GO=OFF \
    -DWITH_PERL5=%{dnf5_with_perl5} \
    -DWITH_PYTHON3=%{dnf5_with_python3} \
    -DWITH_RUBY=OFF \
    -DWITH_SANITIZERS=OFF \
    -DWITH_TESTS=OFF \
    -DWITH_PERFORMANCE_TESTS=OFF \
    -DWITH_DNF5DAEMON_TESTS=OFF

make %{?_smp_mflags}

popd

%check
:

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}

pushd _build
make DESTDIR=%{buildroot} install
popd

# Provide a dnf symlink for convenience.
if [ -x %{buildroot}%{_bindir}/dnf5 ]; then
    ln -snf dnf5 %{buildroot}%{_bindir}/dnf
fi

# Own dirs that libdnf5 creates on runtime.
# Do NOT create empty or stub TOML files - dnf5 will create them as needed.
# Empty/stub files cause parse errors; missing files are handled gracefully.
mkdir -p %{buildroot}%{_prefix}/lib/sysimage/libdnf5
mkdir -p %{buildroot}%{_prefix}/lib/sysimage/libdnf5/comps_groups
mkdir -p %{buildroot}%{_prefix}/lib/sysimage/libdnf5/offline

# Disable the local libdnf5 plugin - it requires a local repo that doesn't exist
mkdir -p %{buildroot}%{_sysconfdir}/dnf/libdnf5-plugins
cat > %{buildroot}%{_sysconfdir}/dnf/libdnf5-plugins/local.conf << 'EOF'
[main]
enabled = false
EOF

rm -f %{buildroot}/usr/share/dnf5/aliases.d/compatibility-plugins.conf || :

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . \( -type f -o -type l \) -print | sed 's|^\./|/|' > %{_builddir}/dnf5-all-files.list

sed -e 's|//\+|/|g' -e 's|/\+$||' -e 's|[[:space:]]*$||' %{_builddir}/dnf5-all-files.list | \
  sort -u > %{_builddir}/dnf5-all-files.list.tmp
mv -f %{_builddir}/dnf5-all-files.list.tmp %{_builddir}/dnf5-all-files.list

test -s %{_builddir}/dnf5-all-files.list

: > %{_builddir}/libdnf5-files.list
: > %{_builddir}/libdnf5-cli-files.list
: > %{_builddir}/libdnf5-devel-files.list
: > %{_builddir}/libdnf5-cli-devel-files.list

%if %{with python3}
: > %{_builddir}/python3-libdnf5-files.list
%endif

%if %{with perl5}
: > %{_builddir}/perl-libdnf5-files.list
%endif

grep -E '^/usr/lib/x86_64-linux-gnu/libdnf5\.so\.' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-files.list || :
grep -E '^/usr/lib/x86_64-linux-gnu/libdnf5($|/)' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-files.list || :
grep -E '^/usr/lib/sysimage/libdnf5($|/)' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-files.list || :
grep -E '^/etc/dnf($|/)' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-files.list || :
grep -E '^/usr/share/dnf5($|/)' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-files.list || :

if [ -d "%{buildroot}%{_prefix}/lib/sysimage/libdnf5/comps_groups" ]; then
  echo "%%dir %{_prefix}/lib/sysimage/libdnf5/comps_groups" >> %{_builddir}/libdnf5-files.list
fi
if [ -d "%{buildroot}%{_prefix}/lib/sysimage/libdnf5/offline" ]; then
  echo "%%dir %{_prefix}/lib/sysimage/libdnf5/offline" >> %{_builddir}/libdnf5-files.list
fi

grep -E '^/usr/lib/x86_64-linux-gnu/libdnf5-cli\.so\.' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-cli-files.list || :
grep -E '^/usr/lib/x86_64-linux-gnu/libdnf5-cli($|/)' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-cli-files.list || :

grep -E '^/usr/include/(dnf5|libdnf5)($|/)' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-devel-files.list || :
grep -E '^/usr/lib/x86_64-linux-gnu/cmake/(dnf5|libdnf5)($|[^/]*?/)' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-devel-files.list || :
grep -E '^/usr/lib/x86_64-linux-gnu/pkgconfig/(dnf5|libdnf5).*\.pc$' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-devel-files.list || :
grep -E '^/usr/lib/x86_64-linux-gnu/libdnf5\.so$' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-devel-files.list || :

grep -E '^/usr/include/libdnf5-cli($|/)' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-cli-devel-files.list || :
grep -E '^/usr/lib/x86_64-linux-gnu/cmake/libdnf5-cli($|[^/]*?/)' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-cli-devel-files.list || :
grep -E '^/usr/lib/x86_64-linux-gnu/pkgconfig/libdnf5-cli.*\.pc$' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-cli-devel-files.list || :
grep -E '^/usr/lib/x86_64-linux-gnu/libdnf5-cli\.so$' %{_builddir}/dnf5-all-files.list >> %{_builddir}/libdnf5-cli-devel-files.list || :

%if %{with python3}
grep -iE '^/usr/lib(64)?(/x86_64-linux-gnu)?/python([0-9\.]+|3)/(site-packages|dist-packages)/.*(dnf5|libdnf5).*' %{_builddir}/dnf5-all-files.list >> %{_builddir}/python3-libdnf5-files.list || :
grep -E '^/usr/lib(64)?(/x86_64-linux-gnu)?/python([0-9\.]+|3)/(site-packages|dist-packages)/.*\.so$' %{_builddir}/dnf5-all-files.list | \
  grep -iE '(dnf5|libdnf5)' >> %{_builddir}/python3-libdnf5-files.list || :
sort -u -o %{_builddir}/python3-libdnf5-files.list %{_builddir}/python3-libdnf5-files.list
test -s %{_builddir}/python3-libdnf5-files.list
%endif

%if %{with perl5}
grep -iE '^/usr/(lib(64)?|share)/perl5/.*(dnf5|libdnf5).*' %{_builddir}/dnf5-all-files.list >> %{_builddir}/perl-libdnf5-files.list || :
grep -iE '^/usr/lib/x86_64-linux-gnu/perl5/.*(dnf5|libdnf5).*' %{_builddir}/dnf5-all-files.list >> %{_builddir}/perl-libdnf5-files.list || :
sed -e 's|//\+|/|g' -e 's|/\+$||' -e 's|[[:space:]]*$||' %{_builddir}/perl-libdnf5-files.list | \
  sort -u > %{_builddir}/perl-libdnf5-files.list.tmp
mv -f %{_builddir}/perl-libdnf5-files.list.tmp %{_builddir}/perl-libdnf5-files.list
test -s %{_builddir}/perl-libdnf5-files.list
%endif

for f in \
  %{_builddir}/libdnf5-files.list \
  %{_builddir}/libdnf5-cli-files.list \
  %{_builddir}/libdnf5-devel-files.list \
  %{_builddir}/libdnf5-cli-devel-files.list
do
  sed -e 's|//\+|/|g' -e 's|/\+$||' -e 's|[[:space:]]*$||' "$f" | sort -u > "$f.tmp"
  mv -f "$f.tmp" "$f"
done

%if %{with python3}
sed -e 's|//\+|/|g' -e 's|/\+$||' -e 's|[[:space:]]*$||' %{_builddir}/python3-libdnf5-files.list | \
  sort -u > %{_builddir}/python3-libdnf5-files.list.tmp
mv -f %{_builddir}/python3-libdnf5-files.list.tmp %{_builddir}/python3-libdnf5-files.list
%endif

test -s %{_builddir}/libdnf5-files.list
test -s %{_builddir}/libdnf5-cli-files.list
test -s %{_builddir}/libdnf5-devel-files.list
test -s %{_builddir}/libdnf5-cli-devel-files.list

grep -vxFf %{_builddir}/libdnf5-files.list %{_builddir}/dnf5-all-files.list | \
  grep -vxFf %{_builddir}/libdnf5-cli-files.list | \
  grep -vxFf %{_builddir}/libdnf5-devel-files.list | \
  grep -vxFf %{_builddir}/libdnf5-cli-devel-files.list \
%if %{with python3}
  | grep -vxFf %{_builddir}/python3-libdnf5-files.list \
%endif
%if %{with perl5}
  | grep -vxFf %{_builddir}/perl-libdnf5-files.list \
%endif
  > %{_builddir}/dnf5-files.list

test -s %{_builddir}/dnf5-files.list

mkdir -p %{_topdir}/SOURCES/dnf5-filelists || :
cp -f %{_builddir}/dnf5-all-files.list %{_topdir}/SOURCES/dnf5-filelists/ || :
cp -f %{_builddir}/*-files.list %{_topdir}/SOURCES/dnf5-filelists/ || :

%files -f %{_builddir}/dnf5-files.list
%defattr(-,root,root)

%files -n libdnf5 -f %{_builddir}/libdnf5-files.list
%defattr(-,root,root)

%files -n libdnf5-cli -f %{_builddir}/libdnf5-cli-files.list
%defattr(-,root,root)

%files -n libdnf5-devel -f %{_builddir}/libdnf5-devel-files.list
%defattr(-,root,root)

%files -n libdnf5-cli-devel -f %{_builddir}/libdnf5-cli-devel-files.list
%defattr(-,root,root)

%if %{with python3}
%files -n python3-libdnf5 -f %{_builddir}/python3-libdnf5-files.list
%defattr(-,root,root)
%endif

%if %{with perl5}
%files -n perl-libdnf5 -f %{_builddir}/perl-libdnf5-files.list
%defattr(-,root,root)
%endif

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 5.3.0.0-1
- Initial packaging for Maquilinux

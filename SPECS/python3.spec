Name:           python3
Version:        3.14.0
Release:        2.m264%{?dist}
Summary:        Python programming language (version 3)

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        Python
URL:            https://www.python.org/
Source0:        https://www.python.org/ftp/python/%{version}/Python-%{version}.tar.xz
Source1:        https://www.python.org/ftp/python/doc/%{version}/python-%{version}-docs-html.tar.bz2

BuildRequires:  expat-devel
BuildRequires:  libffi-devel
BuildRequires:  openssl-devel
BuildRequires:  sqlite-devel
BuildRequires:  zlib-devel

%if "%{_target_cpu}" != "i686"
Provides:       python3-devel = %{version}-%{release}
Provides:       /usr/bin/python
%endif

%description
Python 3 is a powerful, object-oriented programming language used for
scripting, application development, and as a foundation for many tools.

%prep
%setup -q -n Python-%{version}

# Unpack the prebuilt HTML documentation for later installation
if [ -f "%{_sourcedir}/python-%{version}-docs-html.tar.bz2" ]; then
%{__tar} -xf "%{_sourcedir}/python-%{version}-docs-html.tar.bz2" -C %{_builddir}
fi

%build
./configure \
    --prefix=%{_prefix} \
    --enable-shared \
    --with-system-expat \
    --without-static-libpython

make %{?_smp_mflags}

%check
# Skip tests for faster build
:

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

install -d %{buildroot}%{_sysconfdir}
cat > %{buildroot}%{_sysconfdir}/pip.conf << 'EOF'
[global]
root-user-action = ignore
disable-pip-version-check = true
EOF

install -d %{buildroot}%{_datadir}/doc/python-%{version}/html
if [ -d "%{_builddir}/python-%{version}-docs-html" ]; then
  cp -a %{_builddir}/python-%{version}-docs-html/* \
      %{buildroot}%{_datadir}/doc/python-%{version}/html/
fi

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/python3-files.list

%files -f %{_builddir}/python3-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 3.14.0-1.m264
- Initial packaging aligned with MLFS 8.54 instructions.

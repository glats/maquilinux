%define swig_version 4.4.1

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

Name:           swig
Version:        %{swig_version}
Release:        1.m264%{?dist}
Summary:        Simplified Wrapper and Interface Generator

License:        GPL-3.0-or-later
URL:            https://www.swig.org/
Source0:        http://prdownloads.sourceforge.net/swig/swig-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  pcre2

%description
SWIG is a compiler that integrates C and C++ with various scripting languages.
It reads C/C++ declarations and generates wrapper code so that the C/C++ code can
be called from languages such as Python and Perl.

%prep
%setup -q -n swig-%{version}

%build
export CPPFLAGS="${CPPFLAGS:-} -I/usr/include"
export LDFLAGS="${LDFLAGS:-} -L/usr/lib/x86_64-linux-gnu"
export PKG_CONFIG_LIBDIR="/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig"

./configure \
    --prefix=%{_prefix} \
    --disable-static

make %{?_smp_mflags}

%check
:

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . \( -type f -o -type l \) | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/swig-files.list

test -s %{_builddir}/swig-files.list

%files -f %{_builddir}/swig-files.list
%defattr(-,root,root,-)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 4.4.1-1.m264
- Initial swig packaging.

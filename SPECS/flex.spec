Name:           flex
Version:        2.6.4
Release:        1.m264%{?dist}
Summary:        Fast lexical analyzer generator

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        BSD
URL:            https://github.com/westes/flex
Source0:        https://github.com/westes/flex/releases/download/v%{version}/flex-%{version}.tar.gz

%description
Flex is a fast lexical analyzer generator. It is a tool for generating
programs that recognize lexical patterns in text.

%prep
%setup -q -n flex-%{version}

%build
./configure \
    --prefix=%{_prefix} \
    --disable-static \
    --docdir=%{_datadir}/doc/flex-%{version}

make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

# Provide lex compatibility symlinks as requested by MLFS
ln -sv flex %{buildroot}/usr/bin/lex
ln -sv flex.1 %{buildroot}/usr/share/man/man1/lex.1

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/flex-files.list

%files -f %{_builddir}/flex-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.6.4-1.m264
- Initial RPM packaging for flex following MLFS instructions.

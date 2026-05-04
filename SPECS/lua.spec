# SPECS/lua.spec
%define debug_package %{nil}

Name:           lua
Version:        5.4.8
Release:        1.m264%{?dist}
Summary:        Lightweight, embeddable scripting language
License:        MIT
URL:            https://www.lua.org
Source0:        https://www.lua.org/ftp/lua-%{version}.tar.gz
BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  readline-devel
BuildRequires:  ncurses-devel
Requires:       readline

%description
Lua is a lightweight, embeddable scripting language designed for
extensibility. It is commonly used as a configuration language,
a game scripting language, or embedded within applications
requiring a fast and powerful scripting capability.

%prep
%autosetup -p1

%build
make MYCFLAGS="-fPIC" MYLDFLAGS="-L/usr/lib/x86_64-linux-gnu" linux-readline
gcc -shared -o liblua.so.5.4.8 -Wl,--whole-archive liblua.a -Wl,--no-whole-archive -ldl -lm -lreadline -lncurses
ln -sf liblua.so.5.4.8 liblua.so.5.4
ln -sf liblua.so.5.4.8 liblua.so

%install
make INSTALL_TOP=%{buildroot}/usr INSTALL_INC=%{buildroot}/usr/include INSTALL_MAN=%{buildroot}/usr/share/man/man1 install

install -d %{buildroot}/usr/lib
install -m 755 liblua.so.5.4.8 %{buildroot}/usr/lib/
ln -sf liblua.so.5.4.8 %{buildroot}/usr/lib/liblua.so.5.4
ln -sf liblua.so.5.4.8 %{buildroot}/usr/lib/liblua.so

# Create pkgconfig file
cat > %{buildroot}/usr/lib/pkgconfig/lua.pc << 'EOF'
prefix=/usr
exec_prefix=${prefix}
libdir=/usr/lib
includedir=/usr/include

Name: Lua
Description: Lua language library
Version: %{version}
Requires:
Libs: -L${libdir} -llua
Cflags: -I${includedir}
EOF

install -d %{buildroot}/usr/share/licenses/lua-%{version}

%files
/usr/bin/lua
/usr/bin/luac
/usr/lib/liblua.so.5.4.8
/usr/lib/liblua.so.5.4
%dir %attr(0755, root, root) /usr/share/licenses/lua-%{version}
/usr/share/man/man1/lua.1.gz
/usr/share/man/man1/luac.1.gz

%package devel
Summary: Development files for Lua
Requires: lua%{?_isa} = %{version}-%{release}

%files devel
/usr/include/lauxlib.h
/usr/include/lua.h
/usr/include/lua.hpp
/usr/include/luaconf.h
/usr/include/lualib.h
/usr/lib/liblua.so
/usr/lib/pkgconfig/lua.pc

%changelog
* Mon May 04 2026 Maqui Linux <info@maquilinux.org> - 5.4.8-1.m264
- Initial Maqui Linux release with m264 tag
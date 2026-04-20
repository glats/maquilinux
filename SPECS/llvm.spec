Name:           llvm
Version:        19.1.7
Release:        1.m264%{?dist}
Summary:        LLVM compiler infrastructure

%define debug_package %{nil}
%define __os_install_post %{nil}

# LLVM needs large memory, disable parallel builds if needed
# %%define _smp_mflags -j4

License:        Apache-2.0 WITH LLVM-exception OR NCSA
URL:            https://llvm.org/
Source0:        https://github.com/llvm/llvm-project/releases/download/llvmorg-%{version}/llvm-%{version}.src.tar.xz
Source1:        https://github.com/llvm/llvm-project/releases/download/llvmorg-%{version}/cmake-%{version}.src.tar.xz

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  cmake
BuildRequires:  ninja-build
BuildRequires:  python3
BuildRequires:  zlib-devel
BuildRequires:  libxml2-devel

Requires:       zlib
Requires:       libxml2

%description
LLVM is a compiler infrastructure designed for compile-time, link-time, run-time,
and idle-time optimization of programs from arbitrary programming languages.
LLVM is written in C++ and has a modular architecture that allows the creation
of custom passes and backends.

This package includes the LLVM core libraries, the LLVM C API, and headers.

%package devel
Summary:        Development files for LLVM
Requires:       %{name} = %{version}-%{release}
Requires:       zlib-devel
Requires:       libxml2-devel

%description devel
The llvm-devel package contains libraries and header files for developing
applications that use LLVM.

%prep
# Setup requires extracting both archives
%setup -q -n llvm-%{version}.src

# Extract cmake modules to the right place
tar -xf %{SOURCE1}
mkdir -p cmake
mv cmake-%{version}.src/* cmake/ 2>/dev/null || true
rm -rf cmake-%{version}.src

%build
mkdir -p build
cd build

# Configure with minimal set of components for Rust support
cmake -G Ninja .. \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLVM_ENABLE_PROJECTS="" \
    -DLLVM_TARGETS_TO_BUILD="X86;AArch64;ARM" \
    -DLLVM_INCLUDE_TESTS=OFF \
    -DLLVM_INCLUDE_EXAMPLES=OFF \
    -DLLVM_INCLUDE_BENCHMARKS=OFF \
    -DLLVM_ENABLE_BINDINGS=OFF \
    -DLLVM_ENABLE_LIBXML2=ON \
    -DLLVM_ENABLE_ZLIB=ON \
    -DLLVM_BUILD_LLVM_DYLIB=ON \
    -DLLVM_LINK_LLVM_DYLIB=ON \
    -DLLVM_INSTALL_UTILS=ON \
    -DLLVM_BUILD_TOOLS=ON \
    -DLLVM_ENABLE_RTTI=ON \
    -DLLVM_ENABLE_EH=ON \
    -DLLVM_DEFAULT_TARGET_TRIPLE="x86_64-pc-linux-gnu"

# Build - this takes a LONG time (hours)
ninja %{?_smp_mflags}

%install
cd build
DESTDIR=%{buildroot} ninja install

# Remove static libraries to reduce size
rm -f %{buildroot}%{_libdir}/*.a

# Move documentation
mkdir -p %{buildroot}%{_docdir}/%{name}-%{version}
cp -a ../LICENSE.TXT ../README.md %{buildroot}%{_docdir}/%{name}-%{version}/ 2>/dev/null || true

%files
%license LICENSE.TXT
%doc %{_docdir}/%{name}-%{version}
%{_bindir}/llvm-ar
%{_bindir}/llvm-as
%{_bindir}/llvm-config
%{_bindir}/llvm-dis
%{_bindir}/llvm-dlltool
%{_bindir}/llvm-lib
%{_bindir}/llvm-link
%{_bindir}/llvm-lto
%{_bindir}/llvm-lto2
%{_bindir}/llvm-mt
%{_bindir}/llvm-nm
%{_bindir}/llvm-objcopy
%{_bindir}/llvm-objdump
%{_bindir}/llvm-profdata
%{_bindir}/llvm-ranlib
%{_bindir}/llvm-readelf
%{_bindir}/llvm-readobj
%{_bindir}/llvm-strip
%{_bindir}/llvm-symbolizer
%{_bindir}/opt
%{_libdir}/libLLVM.so.*
%{_libdir}/libRemarks.so.*
%{_libdir}/libLTO.so.*
%{_libdir}/LLVMHello.so
%{_libdir}/libLLVM-*.so

%files devel
%{_includedir}/llvm
%{_includedir}/llvm-c
%{_libdir}/libLLVM.so
%{_libdir}/libRemarks.so
%{_libdir}/libLTO.so
%{_libdir}/cmake/llvm
%{_libdir}/cmake/llvm*
%{_datadir}/llvm

%changelog
* Sun Apr 19 2026 Maqui Linux <security@maqui-linux.org> - 19.1.7-1.m264
- Initial build for Maqui Linux 26.4
- Minimal configuration for Rust support (X86/AArch64/ARM targets)

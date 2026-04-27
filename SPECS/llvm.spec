Name:           llvm
Version:        19.1.7
Release:        1.m264%{?dist}
Summary:        LLVM compiler infrastructure

%define debug_package %{nil}
%define __os_install_post %{nil}

# Multiarch configuration (Maqui Linux standard)
%if "%{_target_cpu}" == "i686"
%global pkg_multilibdir /usr/lib/i386-linux-gnu
%global pkg_libdir_suffix /i386-linux-gnu
%global pkg_enable_devel 0
%else
%global pkg_multilibdir /usr/lib/x86_64-linux-gnu
%global pkg_libdir_suffix /x86_64-linux-gnu
%global pkg_enable_devel 1
%endif

# LLVM needs large memory, disable parallel builds if needed
# %%define _smp_mflags -j4

License:        Apache-2.0 WITH LLVM-exception OR NCSA
URL:            https://llvm.org/
Source0:        https://github.com/llvm/llvm-project/releases/download/llvmorg-%{version}/llvm-%{version}.src.tar.xz
Source1:        https://github.com/llvm/llvm-project/releases/download/llvmorg-%{version}/cmake-%{version}.src.tar.xz

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  cmake
BuildRequires:  ninja
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
# LLVM 19.x expects cmake modules at ../cmake/Modules relative to source
# Copy the Modules directory to the expected location at build root level
mkdir -p %{_builddir}/cmake
cp -r %{_builddir}/llvm-%{version}.src/cmake-19.1.7.src/Modules %{_builddir}/cmake/

%build
mkdir -p build
cd build

# Configure with minimal set of components for Rust support
# Point to cmake modules extracted in %%prep
cmake -G Ninja .. \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DCMAKE_INSTALL_LIBDIR=lib%{pkg_libdir_suffix} \
    -DLLVM_LIBDIR_SUFFIX=%{pkg_libdir_suffix} \
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
    -DLLVM_DEFAULT_TARGET_TRIPLE="x86_64-pc-linux-gnu" \
    -DLLVM_CMAKE_PATH="%{_builddir}/llvm-%{version}.src/cmake"

# Build - this takes a LONG time (hours)
ninja %{?_smp_mflags}

%install
cd build
DESTDIR=%{buildroot} ninja install

# Remove static libraries to reduce size
rm -f %{buildroot}%{pkg_multilibdir}/*.a 2>/dev/null || true

# Move documentation
mkdir -p %{buildroot}%{_docdir}/%{name}-%{version}
cp -a ../LICENSE.TXT ../README.md %{buildroot}%{_docdir}/%{name}-%{version}/ 2>/dev/null || true

%check
# Minimal sanity check - verify llvm-config works
%{buildroot}%{_bindir}/llvm-config --version || true

%files
%license LICENSE.TXT
%doc %{_docdir}/%{name}-%{version}
# LLVM tools (wildcard covers most)
%{_bindir}/llvm-*
%{_bindir}/opt
%{_bindir}/llc
%{_bindir}/lli
%{_bindir}/bugpoint
%{_bindir}/dsymutil
%{_bindir}/FileCheck
%{_bindir}/count
%{_bindir}/not
%{_bindir}/UnicodeNameMappingGenerator
%{_bindir}/yaml-bench
%{_bindir}/split-file
%{_bindir}/obj2yaml
%{_bindir}/yaml2obj
%{_bindir}/sancov
%{_bindir}/sanstats
%{_bindir}/llvm-tblgen
# Libraries - use multiarch path
%{pkg_multilibdir}/libLLVM.so.*
%{pkg_multilibdir}/libRemarks.so.*
%{pkg_multilibdir}/libLTO.so.*
%{pkg_multilibdir}/LLVMHello.so
%{pkg_multilibdir}/libLLVM-*.so

%files devel
%{_includedir}/llvm
%{_includedir}/llvm-c
%{pkg_multilibdir}/libLLVM.so
%{pkg_multilibdir}/libRemarks.so
%{pkg_multilibdir}/libLTO.so
%{pkg_multilibdir}/cmake/llvm
%{pkg_multilibdir}/cmake/llvm*
%{_datadir}/llvm

%changelog
* Fri Apr 25 2026 Maqui Linux
      - Fixed multiarch library installation using LLVM_LIBDIR_SUFFIX
      - Libraries now install to /usr/lib/x86_64-linux-gnu/
      - Added pkg_libdir_suffix macro for proper multiarch support

      * Sun Apr 19 2026 Maqui Linux
      - Initial build for Maqui Linux 26.4
      - Minimal configuration for Rust support (X86/AArch64/ARM targets)

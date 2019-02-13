#!/usr/bin/env bash

# install clang and llvm
# pacman -Sy mingw-w64-x86_64-llvm \
#            mingw-w64-x86_64-clang \
#            mingw-w64-x86_64-clang-tools-extra \
#            mingw-w64-x86_64-compiler-rt --noconfirm

# install python3
# pacman -Sy mingw-w64-x86_64-python3 --noconfirm

#install cmake
# pacman -Sy mingw-w64-x86_64-cmake --noconfirm

cd ~
git clone https://github.com/Valloric/YouCompleteMe.git
cd ~/YouCompleteMe
git submodule update --init --recursive
mkdir build
cd build

curl -fLo ../third_party/ycmd/cpp/BoostParts/boost/detail/interlocked.hpp \
    https://raw.githubusercontent.com/Reikion/YouCompleteMe/master/cpp/BoostParts/boost/detail/interlocked.hpp

echo "
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -include cmath")
add_definitions(-DBOOST_PYTHON_SOURCE)
add_definitions(-DBOOST_THREAD_BUILD_DLL)
add_definitions(-DMS_WIN64)" >> ../third_party/ycmd/cpp/CMakeLists.txt

cmake -G "MSYS Makefiles" \
    -DPYTHON_LIBRARY=/mingw64/lib/libpython3.7.dll.a \
    -DPYTHON_INCLUDE_DIR=/mingw64/include/python3.7m \
    -DEXTERNAL_LIBCLANG_PATH=/mingw64/lib/libclang.dll.a \
    -DUSE_CLANG_TIDY=OFF -DUSE_PYTHON2=OFF . ../third_party/ycmd/cpp
make ycm_core

cp ../third_party/ycmd/ycm_core.pyd ../python/

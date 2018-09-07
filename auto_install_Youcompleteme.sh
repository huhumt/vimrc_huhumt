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
cmake -G "Unix Makefiles" \
    -DPYTHON_LIBRARY=/mingw64/lib/libpython3.7.dll.a \
    -DPYTHON_INCLUDE_DIR=/mingw64/include/python3.7m \
    -DEXTERNAL_LIBCLANG_PATH=/mingw64/lib/libclang.dll.a \
    -DUSE_CLANG_TIDY=ON -DUSE_PYTHON2=OFF . ~/YouCompleteMe/third_party/ycmd/cpp
make ycm_core
make ycm_support_libs

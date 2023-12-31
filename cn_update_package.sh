#!/usr/bin/env bash
cd /etc/pacman.d

mingw32="./mirrorlist.mingw32.bak"
if [ ! -f $mingw32 ]
then
    mv mirrorlist.mingw32 $mingw32
fi

mingw64="./mirrorlist.mingw64.bak"
if [ ! -f $mingw64 ]
then
    mv mirrorlist.mingw64 $mingw64
fi

msys="./mirrorlist.msys.bak"
if [ ! -f $msys ]
then
    mv mirrorlist.msys mirrorlist.msys.bak
fi

cp mirrorlist.mingw32.cn mirrorlist.mingw32
cp mirrorlist.mingw64.cn mirrorlist.mingw64
cp mirrorlist.msys.cn mirrorlist.msys

pacman -Syu --noconfirm

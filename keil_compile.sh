#!/usr/bin/env bash

cc="C:\Program Files (x86)\Keil\C251\UV4\Uv4.exe"
target=$(find ../ -iname "*.uvproj")
compile_project="\"$cc\" -b \"$target\" -o output.txt"

eval $compile_project
mv "../mcu/keil/output.txt" "./compile.log"

latest_bin=$(ls -t ../mcu/output/*Ref*app.bin | head -1)
if [ -f "*app.bin" ]
then
    rm -f "./*app.bin"
fi
cp "$latest_bin" "./"

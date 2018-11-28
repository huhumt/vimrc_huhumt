#!/usr/bin/env bash

get_date()
{
    year=$(date +%Y)
    month=$(date +%m)
    day=$(date +%d)
    echo "$year$month$day"
}

compile_project()
{
    cc="C:\Program Files (x86)\Keil\C251\UV4\Uv4.exe"
    target=$(find ../ -iname "*.uvproj")
    compile_project="\"$cc\" -b \"$target\" -o output.txt"
    eval $compile_project
}

copy_log_and_bin()
{
    mv ../mcu/keil/output.txt ./compile.log

    today_date=$(get_date)
    target_bin="../mcu/output/*""$today_date""_app.bin"
    latest_bin=$(ls -t $target_bin | head -1)
    check_bin=$(find ./ -name "*app.bin" | wc -l)
    if [ $check_bin -gt 0 ]
    then
        rm -f ./*app.bin
    fi
    cp "$latest_bin" ./
}

main()
{
    compile_project
    copy_log_and_bin
}

main

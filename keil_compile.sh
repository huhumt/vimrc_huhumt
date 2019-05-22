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
    if [ "$1" = "-v5" ]
    then
        cc="C:\Program Files (x86)\Keil\Ver557\UV4\Uv4.exe"
        printf "\nNow compile project with Keil5:\n"
    else
        cc="C:\Program Files (x86)\Keil\C251\UV4\Uv4.exe"
        printf "\nNow compile project with Keil4:\n"
    fi
    target=$(find ../ -iname "*.uvproj")
    compile_project="\"$cc\" -b \"$target\" -o output.txt"
    eval $compile_project
}

copy_log_and_bin()
{
    mv ../mcu/keil/output.txt ./compile.log

    local target_bin_list=( _app.bin _Bootloader.bin _Pramboot.bin )
    for target_bin in ${target_bin_list[@]}
    do
        local check_bin=$(find ./ -name "*""$target_bin""" | wc -l)
        if [ $check_bin -gt 0 ]
        then
            rm -f ./*$target_bin
        fi

        if [ "$taget_bin" = "_app.bin" ]
        then
            local today_date=$(get_date)
            local app_bin="../mcu/output/*""$today_date""_app.bin"
        else
            local app_bin="../mcu/output/*""$target_bin"""
        fi

        local check_app_bin=$(ls -l $app_bin 2>/dev/null | wc -l)
        if [ $check_app_bin -gt 0 ]
        then
            latest_bin=$(ls -t $app_bin | head -1)
            printf "\tCopy $latest_bin to current direcotry\n"
            cp "$latest_bin" ./
            break
        fi
    done
}

main()
{
    compile_project $1
    copy_log_and_bin
}

main $@

#!/usr/bin/env bash

get_date()
{
    if [ "$1" = "" ]
    then
        local year=$(date +%Y)
        local month=$(date +%m)
        local day=$(date +%d)
    else
        local year=$(date +%Y -r $1)
        local month=$(date +%m -r $1)
        local day=$(date +%d -r $1)
    fi
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
    local today_date=$(get_date)
    local log_filename=$(find ../ -iname "output.txt")
    if [ ! -z "$log_filename" -a "$log_filename" != " " ]
    then
        mv $log_filename ./compile.log
        local last_line=$(tail -n1 compile.log)
        if [[ "$last_line" == *"Target not created"* ]]
        then
            printf "\t $today_date: Failed to compile project, refer to 'compile.log' to see details\n"
            return 1
        fi
    fi

    local target_bin_list=( _app.bin _Bootloader.bin _Pramboot.bin )
    for target_bin in ${target_bin_list[@]}
    do
        local check_bin=$(find ./ -name "*""$target_bin""" | wc -l)
        if [ $check_bin -gt 0 ]
        then
            rm -f ./*$target_bin
        fi

        output_dir=$(find ../ -name "output")
        if [ "$taget_bin" = "_app.bin" ]
        then
            local app_bin="""$output_dir""/FT*""$today_date""_app.bin"
        else
            local app_bin="""$output_dir""/FT*""$target_bin"""
        fi

        local check_app_bin=$(ls -l $app_bin 2>/dev/null | wc -l)
        if [ $check_app_bin -gt 0 ]
        then
            local latest_bin=$(ls -t $app_bin | head -1)
            local bin_date=$(get_date $latest_bin)
            if [ "$bin_date" = "$today_date" ]
            then
                printf "\t $bin_date: Success to compile project, copy '$latest_bin' to current direcotry\n"
                cp "$latest_bin" ./
                return 0
            fi
        fi
    done
    return 2
}

main()
{
    compile_project $1
    copy_log_and_bin
}

main $@

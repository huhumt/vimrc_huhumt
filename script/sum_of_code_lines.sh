#!/usr/bin/env bash

get_file_lines()
{
    local lines=$(cat "$1" | wc -l)
    echo "$lines"
}

main()
{
    local support_file_type=(".h" ".hpp" ".c" ".cpp")
    local total_lines=()
    local total_files=()
    local all_file_lines="0"
    local all_file_num="0"
    local cnt="0"
    for type in ${support_file_type[@]}
    do
        local filename
        local filename_array=$(find "$1" -name "*$type")
        local type_file_lines="0"
        local type_file_num="0"
        for filename in ${filename_array[@]}
        do
            local lines=$(get_file_lines "$filename")
            printf "%6s lines of %s file\n" $lines $filename
            type_file_num=$((type_file_num + 1))
            type_file_lines=$((type_file_lines + lines))
        done

        all_file_num=$((all_file_num + type_file_num))
        all_file_lines=$((all_file_lines + type_file_lines))

        total_lines[$cnt]=$type_file_lines
        total_files[$cnt]=$type_file_num
        cnt=$((cnt + 1))
    done

    printf "\nTotal have %u files with %u lines:\n" $all_file_num $all_file_lines
    for i in $( seq 0 $((${#support_file_type[@]} - 1)))
    do
        if [ ${total_files[$i]} -gt 0 ]
        then
            printf "\t%6d %6s files with %10d total lines\n" ${total_files[$i]} ${support_file_type[$i]} ${total_lines[$i]}
        fi
    done
}

if [ $# -lt 1 ]
then
    printf "Usage: sh sum_of_code_lines directory\n"
    exit
else
    main $1
fi

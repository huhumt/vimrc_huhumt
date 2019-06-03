#!/usr/bin/env bash

get_file_lines()
{
    local lines=$(cat "$1" | wc -l)
    echo "$lines"
}

main()
{
    local support_file_type=(".h" ".hpp" ".c" ".cpp")
    local total_lines=("0" "0" "0" "0")
    local total_files=("0" "0" "0" "0")
    local all_file_lines="0"
    local all_file_num="0"
    local cnt="0"
    for type in ${support_file_type[@]}
    do
        local filename
        local filename_array=$(find "$1" -name "*$type")
        for filename in ${filename_array[@]}
        do
            local lines=$(get_file_lines "$filename")
            printf "%s lines of %s file\n" $lines $filename
            total_lines[cnt]=$((total_lines[cnt] + lines))
            total_files[cnt]=$((total_files[cnt] + 1))
            all_file_lines=$((all_file_lines + lines))
            all_file_num=$((all_file_num + 1))
        done
        cnt=$((cnt + 1))
    done

    printf "\nTotal have %u files with %u lines:\n" $all_file_num $all_file_lines
    for i in $( seq 0 $((${#support_file_type[@]} - 1)))
    do
        if [ ${total_files[i]} -gt 0 ]
        then
            printf "\t------------%d %s files with %d total lines\n" ${total_files[i]} ${support_file_type[i]} ${total_lines[i]}
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

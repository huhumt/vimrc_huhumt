#!/usr/bin/env bash

get_code_lines()
{
    # local lines=$(find "$1" -name "*"$2"" | xargs wc -l 2>&1 > /dev/null)
    local lines=$(find "$1" -name "*"$2"" | wc -l)
    echo "$lines"
}

main()
{
    local support_file_type=(".h" ".hpp" ".c" ".cpp")
    local total_lines="0"
    for type in ${support_file_type[@]}
    do
        local lines=$(get_code_lines "$1" "$type")
        printf "%s lines of %s file\n" $lines $type
        total_lines=$((total_lines + lines))
    done
    printf "\t---------Totally have %d lines of code\n" $total_lines
}

if [ $# -lt 1 ]
then
    printf "Usage: sh sum_of_code_lines directory\n"
    exit
else
    main $1
fi

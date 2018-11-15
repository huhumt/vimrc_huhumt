#!/usr/bin/env bash

do_format()
{
    local header_file_list=$(find $2 -name "*.$1")
    for header_file in ${header_file_list[@]}
    do
        header_file_split_array=(${header_file//\// })
        header_filename=${header_file_split_array[-1]}
        sh "/usr/local/bin/string_replace.sh" "$header_filename" "#include \"$header_file\"" "$2" "--whole-line-mode"
    done
}

main()
{
    local support_type_list=( h hpp )

    for type in ${support_type_list[@]}
    do
        do_format "$type" "$1"
    done
}

if [ $# -lt 1 ]
then
    printf "Usage: format_include.sh directory\n"
    exit
fi

main $@

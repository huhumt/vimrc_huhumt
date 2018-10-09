#!/usr/bin/env bash

check_type()
{
    local par1=$1
    local support_type=( h hpp )
    local file_type="${par1##*.}"
    local type

    for type in ${support_type[@]}
    do
        if [ "$file_type" = "$type" ]
        then
            return 0
        fi
    done
    return 1
}

str_delete_last_char()
{
    local dir_name=$1
    local tail=${dir_name: -1}
    if [ $tail = "/" ]
    then
        dir_name=${dir_name: 0: -1}
    fi
    echo "$dir_name"
}

do_format()
{
    local dir_name=$(str_delete_last_char "$1")
    local dirlist=$(ls $dir_name)
    local dir
    for dir in ${dirlist[@]}
    do
        local filename=$dir_name/$dir
        if [ -d $filename ]
        then
            do_format $filename
        elif [ -f $filename ]
        then
            check_type $filename
            if [ $? -eq 0 ]
            then
                local filename_list=(${filename//// })
                local src=${filename_list[-1]}
                local dst="."
                local length=${#filename_list[@]}
                for ((i=2; i<length; i++))
                do
                    dst+="/${filename_list[$i]}"
                done
                # echo $src $dst $root_directory
                sh /usr/local/bin/string_replace.sh "include \"$src\"" "include \"$dst\"" $root_directory
            fi
        fi
    done
}

if [ $# -lt 1 ]
then
    printf "Usage: format.sh directory\n"
    exit
fi

root_directory=$(str_delete_last_char "$1")
do_format $@

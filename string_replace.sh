#!/usr/bin/env bash

check_type()
{
    local par1=$1
    local support_type=( c cc cpp h hpp )
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

do_replace()
{
    local filename=$1

    check_type $filename
    if [ $? -eq 0 ]
    then
        if [ "$dst_str" = "EmPtYeMpTy" ]
        then
            sed -i 's/'"$src_str"'//g' $filename
        else
            sed -i 's/'"$src_str"'/'"$dst_str"'/g' $filename
        fi
    fi
}

str_replace()
{
    local dirlist=$(ls $1)
    local dir

    for dir in ${dirlist[@]}
    do
        local filename=$1/$dir
        if [ -d $filename ]
        then
            str_replace $filename
        elif [ -f $filename ]
        then
            do_replace $filename
        fi
    done
}

main()
{
    if [ -f $dst_dir ]
    then
        do_replace $dst_dir
    elif [ -d $dst_dir ]
    then
        local len=${#dst_dir}
        local tail=${dst_dir:len-1:1}
        if [ "$tail" = "/" ]
        then
            dst_dir=${dst_dir:0:len-1}
        fi
        str_replace $dst_dir
    fi
}

if [ $# -lt 3 ]
then
    printf "Usage: string_replace.sh src dst filename/directory\n"
    exit
fi

src_str=$1
dst_str=$2
dst_dir=$3

if [ "$src_str" = "" ]
then
    printf "source string can't be empty\n"
fi

if [ "$dst_dir" = "" ]
then
    dst_str="EmPtYeMpTy"
fi

main $src_str $dst_str $dst_dir

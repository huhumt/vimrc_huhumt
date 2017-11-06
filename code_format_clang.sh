#!/usr/bin/env bash

check_type()
{
    local par1=$1
    local support_type=( c cc cpp h hpp )
    local file_type="${par1##*.}"
    local type
    for type in ${support_type[@]}
    do
        if [ $file_type = $type ]
        then
            return 0
        fi
    done
    return 1
}

format_code()
{
    local dirlist=$(ls $1)
    local dir
    for dir in ${dirlist[@]}
    do
        if [ -d $1/$dir ]
        then
            printf "\nDirectory: $1/$dir\n"
            format_code $1/$dir
        elif [ -f $1/$dir ]
        then
            check_type $1/$dir
            if [ $? -eq 0 ]
            then
                clang-format -style=llvm -i $1/$dir
                printf "    success format file: $1/$dir\n"
            else
                printf "    unsupported file type: $1/$dir\n"
            fi
        fi
    done
}

main()
{
    local name
    for name in $1
    do
        if [ -f $name ]
        then
            clang-format -style=llvm -i $name
        elif [ -d $name ]
        then
            len=${#name}
            tail=${name:len-1:1}
            if [ "$tail" = "/" ]
            then
                name=${name:0:len-1}
            fi
            format_code $name
        fi
    done
}

if [ $# -eq 0 ]
then
    printf "Plese give directory or file to do format\n"
    exit
fi

main $@

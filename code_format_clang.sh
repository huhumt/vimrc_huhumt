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

format_method()
{
    local filename=$1
    local method=$2

    if [ "$method" = "clang-format" ]
    then
        clang-format -style=llvm -i $filename
    else
        vim $filename -c "silent Autoformat" -c "wq"
    fi
}

sum_of_file="0"
sum_of_line="0"
format_code()
{
    local dirlist=$(ls $1)
    local dir
    local method=$2

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
                format_method $1/$dir $2
                local lines=$(wc -l < $1/$dir)
                printf "    success format file: $1/$dir, totally has $lines lines\n"
                sum_of_file=$(($sum_of_file+1))
                sum_of_line=$(($sum_of_line+$lines))
            else
                printf "    unsupported file type: $1/$dir\n"
            fi
        fi
    done
}

main()
{
    local name=$1
    local method="vim-clang"

    if [ -f $name ]
    then
        check_type $name
        if [ $? -eq 0 ]
        then
            format_method $name $method
            local lines=$(wc -l < $name)
            printf "    success format file: $name, totally has $lines lines\n"
        else
            printf "    unsupported file type: $name\n"
        fi
    elif [ -d $name ]
    then
        len=${#name}
        tail=${name:len-1:1}
        if [ "$tail" = "/" ]
        then
            name=${name:0:len-1}
        fi
        format_code $name $method
        printf "\nTotally has $sum_of_file files with $sum_of_line lines\n"
    fi
}

if [ $# -eq 0 ]
then
    printf "Plese give directory or file to do format\n"
    printf "Usage: code_format_clang filename/directory\n"
    exit
fi

main $@

#!/usr/bin/env bash

detect_formatter()
{
    local formatter_list=( astyle clang-format )

    for formatter in ${formatter_list[@]}
    do
        type $formatter >/dev/null 2>&1
        if [ $? -eq 0 ]
        then
            echo "--with-$formatter"
            break
        fi
    done
}

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

    if [ "$method" = "--with-clang-format-file" ]
    then
        clang-format -style=file -i $filename
    elif [ "$method" = "--with-clang-format--llvm" ]
    then
        clang-format -style=llvm -i $filename
    elif [ "$method" = "--with-astyle-file" ]
    then
        astyle --options=$root_directory/.astylerc $filename >/dev/null 2>&1
    else
        vim $filename -c "silent Autoformat" -c "wq"
    fi
}

do_format()
{
    local filename=$1
    local method=$2

    check_type $filename
    if [ $? -eq 0 ]
    then
        format_method $filename $method
        local lines=$(wc -l < $filename)
        printf "    success format file: $filename, totally has $lines lines\n"
        sum_of_file=$(($sum_of_file+1))
        sum_of_line=$(($sum_of_line+$lines))
    else
        printf "    unsupported file type: $filename\n"
    fi
}

format_code()
{
    local dirlist=$(ls $1)
    local dir
    local method=$2

    for dir in ${dirlist[@]}
    do
        local filename=$1/$dir
        if [ -d $filename ]
        then
            printf "\nDirectory: $filename\n"
            format_code $filename $method
        elif [ -f $filename ]
        then
            do_format $filename $method
        fi
    done
}

main()
{
    local name=$1
    local method=$2

    if [ "$2" = "" ]
    then
        method=$(detect_formatter)
    fi

    if [ "$method" = "--with-astyle" ]
    then
        if [ -f $root_directory/.astylerc ]
        then
            method+="-file"
        fi
    elif [ "$method" = "--with-clang-format" ]
    then
        if [ -f ./.clang-format ]
        then
            method+="-file"
        else
            method+="-llvm"
        fi
    else
        method="--with-vim"
    fi

    if [ -f $name ]
    then
        do_format $name $method
    elif [ -d $name ]
    then
        len=${#name}
        tail=${name:len-1:1}
        if [ "$tail" = "/" ]
        then
            name=${name:0:len-1}
        fi
        format_code $name $method
        printf "Success format $name with $method\n"
        printf "Totally has $sum_of_file files with $sum_of_line lines\n"
    fi

    if [ -f ./.clang-format ]
    then
        rm ./.clang-format
    fi
}

sum_of_file="0"
sum_of_line="0"
root_directory=$(eval echo ~${SUDO_USER})
if [ $# -eq 0 ]
then
    printf "Plese give directory or file to do format\n"
    printf "Usage: code_format_clang filename/directory --with-vim\n"
    printf "'--with-vim' is optional to use vim plugin to do format\n"
    exit
else
    echo $root_directory
    main $@
fi

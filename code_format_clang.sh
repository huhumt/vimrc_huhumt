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

    if [ "$method" = "clang-format-vim" ]
    then
        vim $filename -c "silent Autoformat" -c "wq"
    elif [ "$method" = "clang-format-file" ]
    then
        clang-format -style=file -i $filename
    else
        clang-format -style=llvm -i $filename
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
    local method="clang-format"

    if [ "$2" = "--with-vim" ]
    then
        method+="-vim"
    else
        if [ ! -f ~/.clang-format ]
        then
            printf "Download clang-format rules from github...\n"
            wget -q -P ~/ https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/.clang-format
        fi

        if [ ! -f ./.clang-format ]
        then
            cp ~/.clang-format ./
        fi

        if [ -f ./.clang-format ]
        then
            method+="-file"
        else
            method+="-llvm"
        fi
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
        printf "\nTotally has $sum_of_file files with $sum_of_line lines\n"
    fi

    if [ -f ./.clang-format ]
    then
        rm ./.clang-format
    fi
}

sum_of_file="0"
sum_of_line="0"
if [ $# -eq 0 ]
then
    printf "Plese give directory or file to do format\n"
    printf "Usage: code_format_clang filename/directory --with-vim\n"
    printf "appendix '--with-vim' is optional to use vim clang plugin,\n"
    printf "otherwise, use system clang-format instead\n"
    exit
fi

main $@

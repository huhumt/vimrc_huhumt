#!/usr/bin/env bash

check_type()
{
    local par1=$1
    local support_type=( c cc cpp h hpp txt )
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
    local src_str_tmp

    check_type $filename
    if [ $? -eq 0 ]
    then
        if [ "$method" = "--whole-line-mode" ]
        then
            src_str_tmp=".*$src_str.*"
        else
            src_str_tmp="$src_str"
        fi

        if [ "$dst_str" = "EmPtYeMpTy" ]
        then
            # sed -i 's/'"$src_str"'//g' $filename
            sed -i "s#$src_str_tmp##g" "$filename"
            printf "replace $src_str with \"\" in $filename\n"
        else
            # sed -i 's/'"$src_str"'/'"$dst_str"'/g' $filename
            sed -i "s#$src_str_tmp#$dst_str#g" "$filename"
            printf "replace $src_str with $dst_str in $filename\n"
        fi
    else
        printf "$filename: Unsupport file type\n"
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

str_add_escape_char()
{
    local char_array=$(echo $1 | sed -e 's#\(.\)#\1\ #g')
    local str_output=""
    for i in $char_array
    do
        if [ "$i" = "\\" ]
        then
            str_output+="\\\\"
        elif [ "$i" = "#" ]
        then
            str_output+="\\#"
        else
            str_output+=$i
        fi
    done
    echo "$str_output"
}

str_handle()
{
    local string_array=($1)
    local str_output=""

    for cur_str in ${string_array[@]}
    do
        str_output+="$(str_add_escape_char $cur_str)"
        str_output+=" "
    done

    local len=${#str_output}
    str_output=${str_output:0:len-1}

    echo "$str_output"
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
    printf "Usage: string_replace.sh src dst filename/directory --whole-line-mode --with-python\n"
    printf "'--whole-line-mode' is optional for replace whole line including src with dst\n"
    printf "'--with-python' is optional to use python to do replace\n"
    exit
fi

src_str=$1
dst_str=$2
dst_dir=$3
method=$4

if [ "${src_str:0:2}" = "--" ] || [ "${dst_str:0:2}" = "--" ] || [ "${dst_dir:0:2}" = "--" ]
then
    printf "Usage: string_replace.sh src dst filename/directory --whole-line-mode --with-python\n"
    printf "'--whole-line-mode' is optional for replace whole line including src with dst\n"
    printf "'--with-python' is optional to use python to do replace\n"
    exit
fi

if [ "$src_str" = "" ]
then
    printf "source string can't be empty\n"
    exit
fi

if [ "$5" = "--with-python" ]
then
    python3 "/usr/local/bin/python_replace.py" "$1" "$2" "$3" "$4"
elif [ "$4" = "--with-python" ]
then
    python3 "/usr/local/bin/python_replace.py" "$1" "$2" "$3"
else
    src_str=$(str_handle "$src_str")

    if [ "$dst_str" = "" ]
    then
        dst_str="EmPtYeMpTy"
    else
        dst_str=$(str_handle "$dst_str")
    fi

    main "$src_str" "$dst_str" "$dst_dir"
fi

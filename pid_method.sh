#!/usr/bin/env bash

pid_get()
{
    local process_name=$1
    local process_list=$(ps aux)

    while read line
    do
        local cur_process=$line

        if [ "${cur_process/"PID"}" != "$cur_process" ]
        then
            local process_header=($line)
        fi

        if [ "${cur_process/$process_name}" != "$cur_process" ]
        then
            local process_name_found=($line)
            break
        fi
    done <<< $process_list

    local cnt="0"
    for element in "${process_header[@]}"
    do
        if [ $element == "PID" ]
        then
            break
        fi
        cnt=$cnt+1
    done

    if [[ ${process_name_found[$cnt]} =~ ^-?[0-9]+$ ]]
    then
        echo ${process_name_found[$cnt]}
    elif [[ ${process_name_found[$cnt+1]} =~ ^-?[0-9]+$ ]]
    then
        echo ${process_name_found[$cnt+1]}
    else
        echo -1
    fi
}

pid_kill()
{
    local cnt="0"

    while [ $cnt -lt 4 ]
    do
        local process_id=$(pid_get $1)

        if [ $process_id -lt 0 ]
        then
            if [ $cnt -eq 0 ]
            then
                printf "Fail to find process of $1\n"
            else
                printf "Successfully kill process of $1 in loop $cnt\n"
            fi
            break
        else
            if [ $cnt -eq 0 ]
            then
                kill $process_id
            elif [ $cnt -eq 1 ]
            then
                kill -15 $process_id
            elif [ $cnt -eq 2 ]
            then
                kill -9 $process_id
            else
                printf "Bad process, fail to kill it"
            fi
        fi
        cnt=$[$cnt+1]
    done
}

main()
{
    pid_kill $1
}

main $@

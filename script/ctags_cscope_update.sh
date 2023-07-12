#!/usr/bin/env bash

update_ctags_cscope()
{
    echo ""

    # generate ctags
    # ctags -Rnf ./tags.new
    ctags -R --languages=C,C++ --c++-kinds=+p --fields=+iaS --extras=+q .

    # generate cscope
    cscope -Rbkq

    # overwrite old file with newest one
    # mv tags.new tags
    # mv cscope.out.new cscope.out

    # take effect on vim
    # vim --servername VIM --remote-expr "ResetCscope()"
    # vim -E -c "silent cscope reset" -c "qa"

    echo "Update code tags"

    # check whether tags file generated
    if [ -e "tags" ]
    then
        echo "...ctags built"
    else
        echo "Fail to build ctags"
    fi

    # check whether cscope.output file exist
    if [ -e "cscope.out" ]
    then
        echo "...cscope built"
    else
        echo "Fail to build cscope"
    fi

    echo "Finish update code tags, let's roll"
}

check_process_status()
{
    return $(ps aux | grep -v grep | grep $1 | wc -l)
}

run_daemon()
{
    # first generate tags and cscope in current directory
    update_ctags_cscope
    # use a counter to record vim inactive time
    local cnt="0"
    # generate tags and cscope files every 10 second
    while true
    do
        # check whether this script is the last one
        process_name="mintty"
        check_process_status $process_name
        if [ $? -eq 0 ]
        then
            break
        fi

        # check whether vim is active
        process_name="vim"
        check_process_status $process_name
        # vim is active, update tags every 10 second
        if [ $? -gt 0 ]
        then
            # update tags and copy to work directory
            cnt="0"
            update_ctags_cscope
            # vim is inactive, stop process
        else
            # wait for 60 second for vim re-active
            if [ $cnt -gt 6 ]
            then
                # or end process
                break
            else
                echo "vim is not in process"
                cnt=$[$cnt+1]
            fi
        fi
        sleep 10
    done

    echo "I need rest, goodbye"
    rm tags* cscope*
}

main()
{
    if [ "$1" = "-d" ]
    then
        # run in background slient
        printf "\n\t...run ctags and cscope update in background slient"
        # run_daemon > /dev/null &
        run_daemon
    else
        update_ctags_cscope
    fi

    # if [ ! -f ./.clang-format ]
    # then
    #     cp $HOME/.clang-format ./
    # fi
}

main $@

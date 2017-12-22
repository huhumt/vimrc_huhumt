#!/usr/bin/env bash

update_ctags_cscope()
{
    echo ""

    # generate ctags
    ctags -Rnf ./tags.new
    # delete old tags and cscope files
    if [ -e "tags" ]
    then
        cp tags tags.old
    fi
    mv tags.new tags

    find ./ -name "cscope*" > /dev/null
    if [ $? -eq 0 ]
    then
        rm cscope*
    fi
    # generate cscope
    cscope -Rbkq

    echo "Update code tags"

    # check whether tags file generated
    find ./ -name "tags" > /dev/null
    if [ $? -eq 0 ]
    then
        echo "...ctags built"
    else
        echo "Fail to build ctags"
    fi

    # check how many cscope file generated
    cs_num=$(find ./ -name "cscope*" | wc -l)
    if [ $cs_num -eq 3 ]
    then
        echo "...cscope built"
    else
        echo "Fail to build cscope"
    fi

    echo "Finish update code tags, let's roll"
}

check_vim_status()
{
    # if vim is on, return 0, otherwise return 1
    vim_on=$(ps aux | grep vim)
}

main()
{
    # first generate tags and cscope in current directory
    update_ctags_cscope
    # use a counter to record vim inactive time
    local cnt="0"
    # generate tags and cscope files every 10 second
    while true
    do
        # check whether vim is active
        check_vim_status
        # 0: on, 1: off
        vim_status=$?
        # vim is active, update tags every 10 second
        if [ $vim_status -eq 0 ]
        then
            # update tags and copy to work directory
            update_ctags_cscope
            # vim is inactive, stop process
        else
            # wait for 60 second for vim re-active
            if [ $cnt -gt 6 ]
            then
                # or end process
                echo "I need rest, goodbye"
                rm tags* cscope*
                break
            else
                echo "vim is not in process"
                cnt=$[$cnt+1]
            fi
        fi
        sleep 10
    done
}

# run in background slient
main $@ > /dev/null &

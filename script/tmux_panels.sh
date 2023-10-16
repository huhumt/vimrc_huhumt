#!/usr/bin/env bash

session="myTmuxSession"
if ! tmux has-session -t "$session" 2>/dev/null
then
    tmux new-session -s "$session" -d
    for i in $(seq 1 5)
    do
        tmux new-window
        if [ "$i" -eq 2 ]; then
            tmux split-window -v -b -l 50%
            # tmux swap-pane -D
            tmux split-window -h -l 15%

            sleep .5
            tmux send-keys -t .0 "neomutt" Enter
            tmux send-keys -t .1 "gcalcli_watch.sh" Enter
            tmux send-keys -t .2 "weechat -d $HOME/.config/weechat" Enter
            tmux select-pane -t .0
        fi

        if [ "$i" -gt 3 ]; then
            tmux split-window -v -b -l 90%
            # tmux swap-pane -D
            tmux split-window -h
        fi
    done

    tmux send-keys "vncserver" Enter
fi

tmux attach-session -d

if ! tmux has-session -t "$session" 2>/dev/null
then
    for id in $(vncserver -list | grep 590 | cut -d' ' -f1)
    do
        vncserver -kill ":$id"
    done

    for name in $(virsh list | grep running | tr -s  ' ' | cut -d' ' -f3)
    do
        virsh destroy "$name"
    done
    reset
fi

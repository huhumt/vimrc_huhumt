#!/usr/bin/env bash

session="mySession"
if ! tmux has-session -t "$session" 2>/dev/null
then
    tmux new-session -s "$session" -d
    for i in $(seq 1 5)
    do
        tmux new-window
        if [ "$i" -eq 2 ]; then
            tmux split-window -v -p 50
            tmux swap-pane -D
            tmux split-window -h -p 8

            sleep .5
            tmux send-keys -t .0 'neomutt' 'C-m'
            tmux send-keys -t .1 'gcalcli_watch.sh' 'C-m'
            tmux send-keys -t .2 'weechat' 'C-m'
            tmux select-pane -t .0
        fi

        if [ "$i" -gt 3 ]; then
            tmux split-window -v -p 10
            tmux swap-pane -D
            tmux split-window -h
        fi
    done
fi

tmux attach-session -d

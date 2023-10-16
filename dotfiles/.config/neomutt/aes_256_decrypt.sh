#!/bin/bash

while true
do
    if msg=$(openssl aes-256-cbc -d -a -iter +4096 -in ~/.config/neomutt/passwords.enc 2>/dev/null)
    then
        echo "$msg"
        break
    fi
done

#!/bin/bash

while true
do
    msg=$(openssl aes-256-cbc -d -a -iter +4096 -in ~/.config/neomutt/passwords.enc 2>/dev/null)
    if [ "$?" -eq 0 ]
    then
        echo "$msg"
        break
    fi
done

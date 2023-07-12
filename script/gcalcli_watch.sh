#!/bin/bash

watch -n 1800 -c -t "gcalcli --config-folder ~/.config/gcalcli/ agenda | tee /tmp/gcalcli_agenda.txt"

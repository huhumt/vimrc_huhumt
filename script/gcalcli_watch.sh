#!/bin/bash

watch -n 1800 -c -t \
  "gcalcli --config-folder ~/.config/gcalcli/ agenda --details location \
    | sed -e 's/(Meeting Room)-Test Place-\(.*\) (.*/\1/g' \
    | sed -e 'N;s/\n.*Location: \(.*\)*$/ (\1)/;P;D' \
    | tee /tmp/gcalcli_agenda.txt"

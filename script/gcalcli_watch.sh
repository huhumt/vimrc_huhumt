#!/bin/bash

# watch -n 1200 -c -t \
#   "(gcalcli --config-folder ~/.config/gcalcli/ agenda --details location; rustnews) \
#     | sed -e 's/(Meeting Room)-Dale House-\(.*\) (.*/\1/g' \
#     | sed -e 'N;s/\n.*Location: \(.*\)*$/ (\1)/;P;D' \
#     | tee /tmp/gcalcli_agenda.txt"

# watch -n 1200 -c -t \
#   "gcalcli --config-folder ~/.config/gcalcli/ agenda --details location \
#     | sed -e 's/(Meeting Room)-Dale House-\(.*\) (.*/\1/g' \
#     | sed -e 'N;s/\n.*Location: \(.*\)*$/ (\1)/;P;D' \
#     | tee /tmp/gcalcli_agenda.txt; \
#     trans --display-from-local-dict"


watch -n 150 -c -t \
  'gcalcli --config-folder $HOME/.config/gcalcli --nocolor \
    agenda --details location --details url \
    | python $HOME/.local/bin/filter_gcalcli.py \
    | tee /tmp/gcalcli_agenda.txt; trans --display-from-local-dict'

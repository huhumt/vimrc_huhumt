#!/usr/bin/env bash

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


watch -n 200 -c -t \
  'cur_hour=$(date +%k); \
  if [ "$cur_hour" -gt "7" ] && [ "$cur_hour" -lt "20" ]; then \
    if cal_event=$(gcalcli --config-folder $HOME/.config/gcalcli \
    --nocolor agenda \
    --details location \
    --details url \
    --details description); then \
      echo "$cal_event" \
        | python $HOME/.local/bin/filter_gcalcli.py \
        | tee /tmp/gcalcli_agenda.txt; trans --display-from-local-dict; \
    fi \
  else printf "Out of working hour, have some rest\n"; \
  fi'

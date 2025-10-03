#!/usr/bin/env bash

watch -n 200 -c -t -x bash -c \
  'cur_hour=$(date +%k)
  this_year=$(date +%y)
  this_month=$(date +%m)
  holiday_title="Happy holiday"
  if [ "$cur_hour" -eq "17" ]; then
    ag --nofilename --nobreak \
    "Request: Holiday \d{2}/${this_month}/${this_year}" \
    "$HOME/.config/neomutt/mails/" | while read -r holiday; do
      holiday_date=$(grep -oP "\d{2}/\d{2}/\d{2}-\d{2}/\d{2}/\d{2}" <<<"$holiday" | tr / -)
      IFS="-" read -r start_day start_month start_year end_day end_month end_year <<<"$holiday_date"
      holiday_exist=$(gcalcli --config-folder "$HOME/.config/gcalcli" \
          --nocolor search "${holiday_title}" \
          "${start_month}/${start_day}/${start_year}" \
          "${end_month}/${end_day}/${end_year}" | xargs)
      if [[ "$holiday_exist" = "No Events Found..." ]]; then
        duration=$((($(date +%s -d "${end_year}${end_month}${end_day}") - $(date +%s -d "${start_year}${start_month}${start_day}")) / 86400 + 1))
        gcalcli --config-folder "$HOME/.config/gcalcli" add \
            --title "${holiday_title}" --color sage \
            --when "${start_month}/${start_day}/${start_year}" \
            --allday --duration ${duration} --noprompt
      fi
    done
  fi
  if [ "$cur_hour" -gt "7" ] && [ "$cur_hour" -lt "20" ]; then
    if cal_event=$(gcalcli --config-folder $HOME/.config/gcalcli \
    --nocolor agenda \
    --details location \
    --details url \
    --details description); then \
      echo "$cal_event" | python $HOME/.local/bin/filter_gcalcli.py \
        | tee /tmp/gcalcli_agenda.txt; trans --display-from-local-dict
    fi
  else printf "Out of working hour [8:00 ~ 20:00], have some rest\n"
  fi'

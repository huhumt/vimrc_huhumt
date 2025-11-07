#!/usr/bin/env bash

watch -n 200 -c -t -x bash -c '
  cur_hour=$(date +%k)

  if [ "$cur_hour" -eq "7" ]; then
    holiday_month_year=$(date "+%m/%y")
    holiday_title="Happy holiday"
    ag --nofilename --nobreak \
      "Request: Holiday \d{2}/${holiday_month_year}" \
      "$HOME/.config/neomutt/mails/" | while read -r holiday; do
      holiday_date=$(grep -oP "\d{2}/\d{2}/\d{2}(-\d{2}/\d{2}/\d{2})?" <<<"$holiday" | tr / -)
      IFS="-" read -r start_day start_month start_year end_day end_month end_year <<<"$holiday_date"
      start_date=$(date +%F -d "${start_month}/${start_day}/${start_year}")

      if [ -n "$end_day" ]; then
        end_date=$(date +%F -d "${end_month}/${end_day}/${end_year}")
        duration=$((($(date +%s -d "${end_date}") - $(date +%s -d "${start_date}")) / 86400 + 1))
      else
        end_date="$(date +%F -d @$(($(date +%s -d "${start_date}") + 86400)))"
        duration=1
      fi

      holiday_exist=$(gcalcli --config-folder "$HOME/.config/gcalcli" --nocolor \
        search "${holiday_title}" "${start_date}" "${end_date}" | xargs)

      if [[ "$holiday_exist" = "No Events Found..." ]]; then
        [ "${duration}" -gt 1 ] && duration_flag="${duration} days" || duration_flag="1 day"
        gcalcli --config-folder "$HOME/.config/gcalcli" add \
          --title "${holiday_title} (${duration_flag})" --color sage \
          --when "${start_date}" --allday --duration ${duration} --noprompt
      fi
    done
  fi

  if [ "$cur_hour" -gt "7" ] && [ "$cur_hour" -lt "20" ]; then
    # email_date=$(date "+%a, %d %b %Y")
    # if gitlab_reply=$(ag --nofilename --nobreak --only-matching \
    #   "Date: ${email_date}[\s\S]+?\K.+commented[^:]*:[\s\S]+?--" \
    #   "$HOME/.config/neomutt/mails" | perl -p0e "s/((\r?\n){2}|=\r?\n|--)//g"); then
    #   echo "[${email_date}] ${gitlab_reply}" >> /tmp/gitlab_comment_notification
    # fi

    if cal_event=$(gcalcli --config-folder $HOME/.config/gcalcli \
    --nocolor --lineart ascii agenda \
    --details location \
    --details url \
    --details description | python $HOME/.local/bin/filter_gcalcli.py); then
      echo "$cal_event" && echo "$cal_event" > /tmp/gcalcli_agenda.txt && trans --display-from-local-dict
    fi
  else
    cat /tmp/gcalcli_agenda.txt
  fi'

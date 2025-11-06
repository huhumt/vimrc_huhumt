# encoding: utf-8
# Author: Lukasz Korecki <lukasz at coffeesounds dot com>
# Homepage: https://github.com/lukaszkorecki/weechat-tmux-notify

# Version: 0.1
#
# Requires Weechat 0.3
# Released under GNU GPL v2
#
# Based (roughly) on http://github.com/tobypadilla/gnotify
# gnotify is derived from notify http://www.weechat.org/files/scripts/notify.py
# Original author: lavaramano <lavaramano AT gmail DOT com>

import weechat
import os
import re
from datetime import datetime, timedelta
from dataclasses import dataclass

weechat.register("tmuxnotify", "lukaszkorecki", "0.1", "GPL",
                 "tmuxnotify: weechat notifications in tmux", "", "")

# script options
settings = {
    "show_hilights": "on",
    "show_priv_msg": "on",
    "dele_msg_file": "on",
}

for option, default_value in settings.items():
    if weechat.config_get_plugin(option) == "":
        weechat.config_set_plugin(option, default_value)

WEECHAT_LOG_FILENAME = "/tmp/weechat_msg.txt"
GCALCLI_LOG_FILENAME = "/tmp/gcalcli_agenda.txt"
FROM_GCALCLI, FROM_IRC = ("=== From gcalcli agenda, reported at: ",
                          "=== From irc message, reported at: "
                          )
GCALCLI_IRC_SEP = f"\n{'='*80}\n"
WEECHAT_CRON_INTERVAL = 3  # in minutes

# Hook privmsg/hilights
# https://weechat.org/files/doc/stable/weechat_plugin_api.en.html#_hook_signal
weechat.hook_signal("weechat_pv", "notify_show", "private message: ")
weechat.hook_signal("weechat_highlight", "notify_show", "highlight message: ")
weechat.hook_signal("input_text_changed", "notify_show", "delete file")
# https://weechat.org/files/doc/stable/weechat_plugin_api.en.html#_hook_timer
weechat.hook_timer(
    WEECHAT_CRON_INTERVAL * 60 * 1000, 60, 0, "cron_timer_cb", "")


@dataclass
class WeechatLogData:
    source: str  # reported from gcalcli or irc
    key: str     # timestamp for gcalcli, name for irc
    value: str   # event for gcalcli, message for irc
    header: str


def delete_weechat_log(report_source):
    try:
        with open(WEECHAT_LOG_FILENAME, "r") as f:
            content = f.read()
            content_list = content.split(GCALCLI_IRC_SEP, 1)
    except FileNotFoundError:
        pass
    else:
        if report_source == FROM_GCALCLI:  # remove head
            if FROM_GCALCLI in content:
                if FROM_IRC in content:
                    remains = content_list[-1].strip()
                else:
                    remains = None
            else:
                return True
        else:  # remove tail
            if FROM_IRC in content:
                if FROM_GCALCLI in content:
                    remains = content_list[0].strip()
                else:
                    remains = None
            else:
                return True

        with open(WEECHAT_LOG_FILENAME, "w") as f:
            f.write(f"{remains}\n" if remains else "")


def update_gcalcli_log(new_msg, content, force_update=False):
    head = content[0].strip()
    new_msg_lines = len(new_msg.splitlines())
    if head.startswith("<") and head.endswith(">"):
        if force_update:
            irc_msg = ''.join(content[new_msg_lines:])
            return f"{new_msg}{irc_msg}"
        else:
            return None
    else:
        return f"{new_msg}{GCALCLI_IRC_SEP}\n{''.join(content)}"


def update_irc_log(new_msg, content):
    tail = content[-1].strip()
    if tail.startswith("[") and tail.endswith("]"):
        return f"{''.join(content[:-1])}{new_msg}"
    else:
        return f"{''.join(content)}\n{GCALCLI_IRC_SEP}{new_msg}"


def notify_cmd_hyperlink(message):
    hyperlink = '<a href=\"{}\">{}</a>'
    for url in re.findall(r'((https?|s?ftps?)://[^\s]+)', message):
        if url[0][-1] in [",", ".", ")", "]", "}", "?", "'", '"']:
            target_url = url[0][:-1]
        else:
            target_url = url[0]
        if len(target_url) > 64:
            linked_name = f"{target_url[:32]}...{target_url[-16:]}"
        else:
            linked_name = target_url
        message = message.replace(
            target_url, hyperlink.format(target_url, linked_name))
    return message


def notify_event(msg_from, new_msg):
    notify_cmd_list = [
        ("tmux display-popup -E -B -xC -yS -w 30% -h 20% "
         "-s fg=colour220,bg=colour243 "
         f"""'echo "{msg_from}\n  {new_msg}";
         stty -echo;sleep 3;stty echo'"""),

        (f"notify-send -t 10000 -i 'user-idle' "
         f"'{msg_from}' '{notify_cmd_hyperlink(new_msg)}'"),

        f"""tmux display-message -d 5000 '{re.sub(" +", " ", new_msg)}' &""",
    ]

    for cmd in notify_cmd_list:
        os.popen(cmd)


def update_weechat_log(weechat_log_data, new_msg_prefix=""):
    today_date = datetime.today()
    new_msg = re.sub(
        r'[`]', '', f"{weechat_log_data.key}: {weechat_log_data.value}")
    short_msg = new_msg[:32].strip()
    header = f"{weechat_log_data.header}{today_date.strftime('%a %b %d %H:%M')}"

    if weechat_log_data.source == FROM_GCALCLI:
        out_msg = f"<{short_msg}>\n{header}\n{new_msg}\n"
    else:
        out_msg = f"{header}\n{new_msg_prefix}{new_msg}\n[{short_msg}]\n"

    try:
        with open(WEECHAT_LOG_FILENAME, "r") as f:
            content = f.readlines()
    except FileNotFoundError:
        pass
    else:
        if content:
            if weechat_log_data.source == FROM_GCALCLI:
                cur_hour, cur_minute = weechat_log_data.key.split(":")
                event_time = today_date.replace(
                    hour=int(cur_hour), minute=int(cur_minute))
                delta_seconds = abs((today_date - event_time).total_seconds())
                out_msg = update_gcalcli_log(
                    out_msg,
                    content,
                    delta_seconds < WEECHAT_CRON_INTERVAL * 60
                )
            else:
                out_msg = update_irc_log(out_msg, content)

    if out_msg:
        with open(WEECHAT_LOG_FILENAME, "w") as f:
            f.write(out_msg)
        notify_event(weechat_log_data.source, new_msg)


def parse_today_event():
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    today_date = datetime.today()

    # before 8:00AM or after 8:00PM, it's out of work hour
    if today_date.hour not in range(8, 20):
        return None, None

    try:
        with open(GCALCLI_LOG_FILENAME, "r") as r_fd:
            content = ansi_escape.sub("", r_fd.read()).strip()
    except FileNotFoundError:
        pass
    else:
        if content.startswith(today_date.strftime("%a %b %d")):
            re_event = r"(?P<hour>\d{1,2}):(?P<minute>\d{2})\s+(?P<event>.*)"
            for cur_hour, cur_minute, cur_event in filter(
                    lambda x: all(x), re.findall(re_event, content)):
                print(cur_hour, cur_minute, cur_event)
                event_time = today_date.replace(
                    hour=int(cur_hour), minute=int(cur_minute))
                reminder_s = (
                    event_time - timedelta(minutes=WEECHAT_CRON_INTERVAL * 4))
                reminder_e = (
                    event_time + timedelta(minutes=WEECHAT_CRON_INTERVAL * 2))
                if today_date > reminder_s and today_date < reminder_e:
                    return f"{cur_hour}:{cur_minute}", cur_event.strip()
    return None, None


def cron_timer_cb(data, remaining_calls):
    key, value = parse_today_event()
    if key and value:
        update_weechat_log(
            WeechatLogData(FROM_GCALCLI, key, value, FROM_GCALCLI)
        )
    else:
        delete_weechat_log(FROM_GCALCLI)
    return weechat.WEECHAT_RC_OK


def notify_show(data, signal, message):
    """Sends highlight message to be printed on notification"""

    if ((weechat.config_get_plugin('show_hilights') == "on"
         and signal == "weechat_highlight")
            or (weechat.config_get_plugin('show_priv_msg') == "on"
                and signal == "weechat_pv")):
        m = message.split("\t", 1)
        name = m[0].strip()
        msg = m[1].replace("'", "").strip()

        if name == "*":
            name = msg.split()[0]
        elif (name == "*status") or (name == "--" and msg.startswith("irc")):
            return weechat.WEECHAT_RC_OK

        if signal == "weechat_pv":
            COLOUR_OFF = '\033[0m'
            COLOUR_YELLOW_UNDERLINE = '\033[4;33m'
            new_msg_prefix = f"{COLOUR_YELLOW_UNDERLINE}pm: {COLOUR_OFF}"
        else:
            new_msg_prefix = ""
        update_weechat_log(
            WeechatLogData(FROM_IRC, name, msg, FROM_IRC), new_msg_prefix
        )
    elif (weechat.config_get_plugin('dele_msg_file') == "on"
            and signal == "input_text_changed"):
        delete_weechat_log(FROM_IRC)
    return weechat.WEECHAT_RC_OK

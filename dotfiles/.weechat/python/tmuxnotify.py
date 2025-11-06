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
from typing import Optional

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
FROM_SOURCE_TEMPLATE = ("=== From {source}, reported at: ")
MODE_APPEND, MODE_REPLACE, MODE_DELETE = range(3)
GCALCLI_IRC_SEP = ('=' * 80)
WEECHAT_CRON_INTERVAL = 5  # in minutes

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
    # reported from gcalcli or irc
    source: str
    # (HH:MM, event) for gcalcli, (name, msg) for irc
    logs: Optional[tuple] = None
    # update log file mode, can be append, replace and delete
    mode: Optional[int] = MODE_DELETE
    # short message sep tuple, for example ('<', '>')
    sep: Optional[tuple] = None


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


def remove_colour(input_str):
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", input_str).strip()


def update_weechat_log(log_cls: WeechatLogData):
    re_log = re.compile(
        r'(?P<first>[\s\S]*?)'
        fr'(?P<msg>{log_cls.source}[\s\S]+?{GCALCLI_IRC_SEP})'
        r'(?P<last>[\s\S]*?)'
    )

    try:
        with open(WEECHAT_LOG_FILENAME, "r") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""

    if log_cls.logs and log_cls.mode != MODE_DELETE:
        header = log_cls.source + datetime.now().strftime('%a %b %d %H:%M')
        new_msg = ": ".join(log_cls.logs).replace('`', '')
        out_msg = remove_colour(new_msg)
        notify_event(log_cls.source, out_msg)
        short_msg = f"{log_cls.sep[0]}{out_msg[:32]}{log_cls.sep[1]}"

        if log := re_log.findall(content):
            old_msg_list = list(log[0])
            if log_cls.mode == MODE_APPEND:
                # remove old_header, old_short_msg, GCALCLI_IRC_SEP
                old_msg_lines = old_msg_list[1].splitlines()[1:-2]
                old_msg_list[1] = os.linesep.join(old_msg_lines + [new_msg])
            else:
                old_msg_list[1] = new_msg
            msg_list = [header] + [m for m in old_msg_list if m]
        else:
            msg_list = ([content] if content else []) + [header, new_msg]

        msg_list += [short_msg, GCALCLI_IRC_SEP]
        with open(WEECHAT_LOG_FILENAME, "w") as f:
            f.write(os.linesep.join(msg_list))
    else:
        if log := re_log.findall(content):
            with open(WEECHAT_LOG_FILENAME, "w") as f:
                f.write(content.replace(log[0][1], "").strip())


def parse_today_event():
    today_date = datetime.today()

    # before 8:00AM or after 8:00PM, it's out of work hour
    if today_date.hour not in range(8, 20):
        return None

    try:
        with open(GCALCLI_LOG_FILENAME, "r") as r_fd:
            content = remove_colour(r_fd.read())
    except FileNotFoundError:
        pass
    else:
        if content.startswith(today_date.strftime("%a %b %d")):
            re_event = r"(?P<hour>\d{1,2}):(?P<minute>\d{2})\s+(?P<event>.*)"
            for cur_hour, cur_minute, cur_event in filter(
                    lambda x: all(x), re.findall(re_event, content)):
                event_time = today_date.replace(
                    hour=int(cur_hour), minute=int(cur_minute))
                reminder_s = (
                    event_time - timedelta(minutes=WEECHAT_CRON_INTERVAL * 4))
                reminder_e = (
                    event_time + timedelta(minutes=WEECHAT_CRON_INTERVAL * 2))
                if today_date > reminder_s and today_date < reminder_e:
                    return (f"{cur_hour}:{cur_minute}", cur_event.strip())
    return None


def cron_timer_cb(data, remaining_calls):
    update_weechat_log(WeechatLogData(
        source=FROM_SOURCE_TEMPLATE.format("gcalcli agenda"),
        logs=parse_today_event(),
        mode=MODE_REPLACE,
        sep=('<', '>')
    ))
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
            name = f"{COLOUR_YELLOW_UNDERLINE}pm: {COLOUR_OFF}{name}"
        update_weechat_log(WeechatLogData(
            source=FROM_SOURCE_TEMPLATE.format("IRC message"),
            logs=(name, msg),
            mode=MODE_APPEND,
            sep=('[', ']')
        ))
    elif (weechat.config_get_plugin('dele_msg_file') == "on"
            and signal == "input_text_changed"):
        update_weechat_log(
            WeechatLogData(source=FROM_SOURCE_TEMPLATE.format("IRC message")))
    return weechat.WEECHAT_RC_OK

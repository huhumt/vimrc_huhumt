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

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

import weechat
import os
import re

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
FROM_SOURCE_TEMPLATE = ("=== From {log_source}, reported at: ")
FROM_GCALCLI, FROM_IRC, FROM_GITLAB = (
    FROM_SOURCE_TEMPLATE.format(log_source="gcalcli agenda"),
    FROM_SOURCE_TEMPLATE.format(log_source="IRC message"),
    FROM_SOURCE_TEMPLATE.format(log_source="gitlab comment")
)
MODE_APPEND, MODE_REPLACE, MODE_DELETE, MODE_DELETE_SHORT_MSG = range(4)
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
    # update log file mode, can be append, replace and delete
    mode: int = MODE_DELETE
    # short message header, for example: IRC, Git
    short_header: str = ""
    # (HH:MM, event) for gcalcli, (name, msg) for irc
    logs: Optional[tuple] = None
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
        fr'(?P<first>[\s\S]+?{GCALCLI_IRC_SEP})?'
        fr'(?P<msg>(?:\r?\n)?{log_cls.source}[\s\S]+?{GCALCLI_IRC_SEP})'
        r'(?P<last>[\s\S]*)'
    )

    try:
        with open(WEECHAT_LOG_FILENAME, "r") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""

    if log_cls.logs and log_cls.sep and log_cls.mode < MODE_DELETE:
        if (new_msg := ": ".join(log_cls.logs).replace('`', '')) in content:
            return  # avoid duplicated message

        out_msg = remove_colour(new_msg)
        notify_event(log_cls.source, out_msg)
        datetime_format = '%a %m %d %Y %H:%M'

        short_msg = (
            f"{log_cls.sep[0]}"
            f"{log_cls.short_header}{out_msg[:32].strip()}"
            f"{log_cls.sep[1]}"
        )
        new_msg_lines = [
            log_cls.source + datetime.now().strftime(datetime_format),
            new_msg, short_msg, GCALCLI_IRC_SEP
        ]

        if log := re_log.findall(content):
            msg_list = list(log[0])
            old_msg_lines = msg_list[1].strip().splitlines()
            a_week_ago = datetime.now() - timedelta(days=7)
            _, m, d, y, _ = old_msg_lines[0].split(log_cls.source)[-1].split()
            old_msg_date = a_week_ago.replace(
                year=int(y), month=int(m), day=int(d))
            # if old msg is too old, replace it rather than append
            if log_cls.mode == MODE_APPEND and old_msg_date > a_week_ago:
                # remove old_short_msg, GCALCLI_IRC_SEP, keeping old header
                new_msg_lines[0:1] = old_msg_lines[:-2]
            msg_list[1:2] = new_msg_lines
        else:
            # put gitlab message in head
            if log_cls.source == FROM_GITLAB:
                msg_list = new_msg_lines + ([content] if content else [])
            else:
                msg_list = ([content] if content else []) + new_msg_lines
    else:
        if not (log := re_log.findall(content)):
            return

        msg_list = [log[0][0], log[0][-1]]
        if log_cls.mode == MODE_DELETE_SHORT_MSG:
            re_short = fr'(?P<short_msg>(?:<.*>|\[.*\])\s+){GCALCLI_IRC_SEP}'
            if short_msg := re.findall(re_short, log[0][1]):
                msg_list.insert(1, log[0][1].replace(short_msg[0], ''))
            else:
                return

    if new_msg_list := [m.strip() for m in msg_list if m]:
        with open(WEECHAT_LOG_FILENAME, "w") as f:
            f.write(os.linesep.join(new_msg_list))


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


def gitlab_comment_from_email(email_dir=".config/neomutt/mails"):
    email_date = datetime.today().strftime("%a, %d %b %Y")
    re_comment = (fr'Date: {email_date}[\s\S]+?'
                  r'\r?\n(?P<name>.+)commented[^:]*:(?P<comment>[\s\S]+?)--')
    email_list = [m for m in Path(email_dir).rglob("*") if m.is_file()]
    comment_list = list()
    for email in email_list:
        with open(email, 'r', encoding='utf-8', errors='ignore') as f:
            for name, comment in re.findall(re_comment, f.read()):
                comment = re.sub(r'(=\r?\n)', '', comment.strip())
                comment_list += [(name.strip(), comment.splitlines()[0])]
    return comment_list


def cron_timer_cb(data, remaining_calls):
    update_weechat_log(WeechatLogData(
        FROM_GCALCLI, MODE_REPLACE, "", parse_today_event(), ('<', '>')))
    for gitlab_comment in gitlab_comment_from_email():
        update_weechat_log(WeechatLogData(
            FROM_GITLAB, MODE_APPEND, "Gitlab: ", gitlab_comment, ('[', ']')))
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
            FROM_IRC, MODE_APPEND, "IRC: ", (name, msg), ('[', ']')))
    elif (weechat.config_get_plugin('dele_msg_file') == "on"
            and signal == "input_text_changed"):
        update_weechat_log(WeechatLogData(FROM_IRC, MODE_DELETE_SHORT_MSG))
        update_weechat_log(WeechatLogData(FROM_GITLAB, MODE_DELETE_SHORT_MSG))
    return weechat.WEECHAT_RC_OK

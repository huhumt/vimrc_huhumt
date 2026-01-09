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
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

import subprocess
import weechat
import json
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

FROM_IRC, FROM_GCALCLI, FROM_GITLAB = (
    "From irc message", "From gcalcli agenda", "From gitlab comment")
MODE_REPLACE, MODE_APPEND, MODE_DELETE, MODE_DELETE_SHORT_MSG = range(4)
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
    # reported from gcalcli, irc or gitlab
    source: str
    # process mode
    mode: int = MODE_DELETE_SHORT_MSG
    # (HH:MM, event) for gcalcli, (name, msg) for irc and gitlab
    log: Optional[str] = None
    # short message header template, for example: <IRC: (msg)>, [Git: <msg>]
    short_header_template: Optional[str] = None


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


def update_weechat_log(log: WeechatLogData, filename="/tmp/weechat_msg.json"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            file_log_dict: OrderedDict = json.load(f)
    except FileNotFoundError:
        file_log_dict = OrderedDict()

    short_msg_key = "short_msg"
    log_dict = file_log_dict.get(log.source) or {}
    # if not in delete mode but log.log is invalid, switch to delete mode
    if log.mode >= MODE_DELETE or (not log.log):
        if log.mode == MODE_DELETE_SHORT_MSG:
            log_dict.update({short_msg_key: ""})  # delete short msg only
        else:
            file_log_dict.update({log.source: ""})  # delete all
    else:
        full_msg_key = "messages"
        full_msg = log_dict.get(full_msg_key) or {}

        new_msg = log.log.replace('`', '').strip()
        # ignore duplicated message if not in delete mode
        if (out_msg := remove_colour(new_msg)) in full_msg.values():
            return None

        notify_event(log.source, new_msg)
        short_msg = (log.short_header_template or "").format(out_msg[:32])
        new_msg_dict = {datetime.now().strftime("%Y%m%dT%H%M%S%fZ"): out_msg}

        if log.mode == MODE_REPLACE or (not log_dict):
            file_log_dict.update({log.source: {
                short_msg_key: short_msg, full_msg_key: new_msg_dict}})
        else:  # append mode, and key already in
            if len(full_msg) > 30:  # too many logs
                oldest_key = list(full_msg.keys())[0]
                full_msg.pop(oldest_key)  # remove oldest log
            full_msg.update(new_msg_dict)
            log_dict.update({short_msg_key: short_msg, full_msg_key: full_msg})
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(file_log_dict, f, indent=4)


def parse_today_event():
    today_date = datetime.today()
    re_event = r"(?P<hour>[^:\r\n]+):(?P<minute>\d{2})?[: ]+(?P<event>.+)"

    today_event = subprocess.run([
        "python",
        os.path.join(os.path.expanduser('~'), ".local/bin/filter_gcalcli.py"),
        "--from-file",
        "--out-event-only"
    ], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()

    for cur_hour, cur_minute, cur_event in filter(
            lambda x: all(x), re.findall(re_event, today_event)):
        e_t = today_date.replace(hour=int(cur_hour), minute=int(cur_minute))
        r_s = e_t - timedelta(minutes=WEECHAT_CRON_INTERVAL * 4)
        r_e = e_t + timedelta(minutes=WEECHAT_CRON_INTERVAL * 2)
        if today_date > r_s and today_date < r_e:
            return f"{cur_hour}:{cur_minute} {cur_event.strip()}"


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
                comment_list += [f"{name.strip()} {comment.splitlines()[0]}"]
    return comment_list


def cron_timer_cb(data, remaining_calls):
    update_weechat_log(WeechatLogData(
        FROM_GCALCLI, MODE_REPLACE, parse_today_event(), "<{}>"))
    for gitlab_comment in gitlab_comment_from_email():
        update_weechat_log(WeechatLogData(
            FROM_GITLAB, MODE_APPEND, gitlab_comment, "[Gitlab: {}]"))
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

        update_weechat_log(WeechatLogData(
            FROM_IRC, MODE_APPEND, f"{name}: {msg}", "[IRC: {}]"))
    elif (weechat.config_get_plugin('dele_msg_file') == "on"
            and signal == "input_text_changed"):
        update_weechat_log(WeechatLogData(FROM_IRC, MODE_DELETE_SHORT_MSG))
        update_weechat_log(WeechatLogData(FROM_GITLAB, MODE_DELETE_SHORT_MSG))
    return weechat.WEECHAT_RC_OK

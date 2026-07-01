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
    log: Optional[dict] = None
    # short message header template, for example: <IRC: (msg)>, [Git: <msg>]
    short_header_template: Optional[str] = None
    # enable report duplicated event
    enable_duplicated_event: Optional[bool] = False


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
    if msg_from and new_msg:
        for cmd in [
            ("tmux display-popup -E -B -xC -yS -w 30% -h 20% "
             "-s fg=colour220,bg=colour243 "
             f"""'echo "{msg_from}\n  {new_msg}";
             stty -echo;sleep 3;stty echo'"""),

            (f"notify-send -t 10000 -i 'user-idle' "
             f"'{msg_from}' '{notify_cmd_hyperlink(new_msg)}'"),

            f"""tmux display-message -d 5000 '{re.sub(" +", " ", new_msg)}' &""",
        ]:
            os.popen(cmd)


def remove_colour(input_str):
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", input_str.replace('`', '')).strip()


def update_weechat_log(log: WeechatLogData, filename="/tmp/weechat_msg.json"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            file_log_dict: OrderedDict = json.load(f)
    except FileNotFoundError:
        file_log_dict = OrderedDict()

    short_msg_key = "short_msg"
    full_msg_key = "messages"

    log_dict = file_log_dict.get(log.source) or {}
    full_msg = log_dict.get(full_msg_key) or {}

    if log.mode == MODE_DELETE_SHORT_MSG:
        if short_msg_key in log_dict:
            log_dict.pop(short_msg_key)  # delete short msg only
        else:
            return None
    # if not in delete mode but log.log is invalid, switch to delete mode
    elif log.mode == MODE_DELETE or (not log.log):
        file_log_dict.update({log.source: {}})  # delete all
    else:
        new_msg_set = set()
        if "weather" in log.log:
            pre_all_event = list(log_dict.get("all_event", {}).keys())
            cur_all_event = list(log.log.get("all_event", {}).keys())
            if pre_all_event:
                for k, v in log_dict.get("all_event", {}).items():
                    if v > 0:
                        key = remove_colour(k)
                        new_msg_set.add(key)
                        log.log["all_event"].update({key: v - 1})
                for new_event in set(cur_all_event).difference(pre_all_event):
                    key = remove_colour(new_event)
                    new_msg_set.add(key)
                    log.log["all_event"].update({key: 20})
            file_log_dict.update({log.source: log.log})
        else:
            for k, v in log.log.items():
                out_msg = remove_colour(f"{v}: {k}")

                # ignore duplicated message if not in delete mode
                if (out_msg not in full_msg.values()) or log.enable_duplicated_event:
                    new_msg_set.add(out_msg)

        notify_event(log.source, "\n".join(new_msg_set))
        for new_msg in new_msg_set:
            short_msg = (log.short_header_template or "").format(new_msg[:32])
            new_msg_dict = {
                datetime.now().strftime("%Y%m%dT%H%M%S%fZ"): new_msg
            }

            if log.mode == MODE_REPLACE or (not log_dict):
                if log.source in file_log_dict:
                    file_log_dict[log.source].update({
                        short_msg_key: short_msg,
                        full_msg_key: new_msg_dict
                    })
                else:
                    file_log_dict.update({
                        log.source: {
                            short_msg_key: short_msg,
                            full_msg_key: new_msg_dict
                        }
                    })
            else:  # append mode, and key already in
                full_msg.update(new_msg_dict)
                if (to_remove := len(full_msg) - 30) > 0:  # too many logs
                    for to_remove_key in list(full_msg.keys())[:to_remove]:
                        full_msg.pop(to_remove_key)  # remove oldest log
                log_dict.update({
                    short_msg_key: short_msg,
                    full_msg_key: full_msg
                })
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(file_log_dict, f, indent=4, ensure_ascii=False)


def parse_today_event():
    today_date = datetime.today()
    re_event = r"(?P<hour>[^:\r\n]+):(?P<minute>\d{2})?[: ]+(?P<event>.+)"
    event_dict = {"weather": None, "all_event": {}}

    today_event = subprocess.run([
        "python",
        os.path.join(os.path.expanduser('~'), ".local/bin/filter_gcalcli.py"),
        "--from-file",
        "--out-event-only",
        "--days-later", "0"
    ], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()

    for cur_hour, cur_minute, cur_event in re.findall(re_event, today_event):
        cur_hour = cur_hour.strip()
        cur_minute = cur_minute.strip()
        cur_event = cur_event.strip()

        if all([cur_hour, cur_minute, cur_event]):
            event_dict["all_event"].update({f"{cur_hour}:{cur_minute} {cur_event}": 0})
            e_t = today_date.replace(
                hour=int(cur_hour), minute=int(cur_minute))
            r_s = e_t - timedelta(minutes=WEECHAT_CRON_INTERVAL * 4)
            r_e = e_t + timedelta(minutes=WEECHAT_CRON_INTERVAL * 2)
            if today_date > r_s and today_date < r_e:
                return {cur_event: f"{cur_hour}:{cur_minute}"}
        else:  # all day event
            if f"{cur_hour}{cur_minute}".lower() == "weather":
                weather_list = cur_event.split()
                event_dict["weather"] = f"{weather_list[0]}  {weather_list[-1]}"
    return event_dict if event_dict.get("weather") else None


def gitlab_comment_from_email(email_dir=".config/neomutt/mails"):
    minutes_ago = datetime.today() - timedelta(minutes=WEECHAT_CRON_INTERVAL*20)
    re_comment = (
        r"Date: (?P<date>.+ \d+:\d+)[\s\S]+?"
        r"\r?\n(?P<name>.+)commented[^:]*:(?P<comment>[\s\S]+?)--"
    )
    email_list = [
        m for m in Path.home().joinpath(email_dir).rglob("[a-z0-9A-Z]*") if m.is_file()
    ]
    comment_dict = {}
    for email in email_list:
        with open(email, "r", encoding="utf-8", errors="ignore") as f:
            for date, name, comment in re.findall(re_comment, f.read()):
                if datetime.strptime(date, "%a, %d %b %Y %H:%M") > minutes_ago:
                    comment = re.sub(r"(=\r?\n)", "", comment.strip())
                    comment_dict.update({comment.splitlines()[0]: name.strip()})
    return comment_dict


def cron_timer_cb(data, remaining_calls):
    update_weechat_log(WeechatLogData(
        FROM_GCALCLI, MODE_REPLACE, parse_today_event(), "<{}>", True))
    update_weechat_log(WeechatLogData(
        FROM_GITLAB, MODE_APPEND, gitlab_comment_from_email(), "[Gitlab: {}]", False))
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
            FROM_IRC, MODE_APPEND, {msg: name}, "[IRC: {}]", True))
    elif (weechat.config_get_plugin('dele_msg_file') == "on"
            and signal == "input_text_changed"):
        update_weechat_log(WeechatLogData(FROM_IRC, MODE_DELETE_SHORT_MSG))
        update_weechat_log(WeechatLogData(FROM_GITLAB, MODE_DELETE_SHORT_MSG))
    return weechat.WEECHAT_RC_OK

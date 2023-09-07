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

# Hook privmsg/hilights
# https://weechat.org/files/doc/stable/weechat_plugin_api.en.html#_hook_signal
weechat.hook_signal("weechat_pv", "notify_show", "private message: ")
weechat.hook_signal("weechat_highlight", "notify_show", "highlight message: ")
weechat.hook_signal("input_text_changed", "notify_show", "delete file")
# https://weechat.org/files/doc/stable/weechat_plugin_api.en.html#_hook_timer
weechat.hook_timer(180 * 1000, 60, 0, "cron_timer_cb", "")


@dataclass
class WeechatLogData:
    key: str
    value: str
    header: str


def delete_weechat_log(filename="/tmp/weechat_msg.txt"):
    try:
        with open(filename, "r+") as f:
            content = f.readlines()
            if len(content) > 1:
                f.seek(0)
                f.write(content[0])
                f.truncate()
    except FileNotFoundError:
        pass


def update_weechat_log(weechat_log_data, filename="/tmp/weechat_msg.txt"):
    today_m_d = datetime.today().strftime("%a %b %d")
    now_h_m = datetime.now().time()
    msg_list = [f'{weechat_log_data.header}: reported at ',
                f'{today_m_d} {now_h_m.strftime("%H:%M")}\n']
    new_msg = f"{weechat_log_data.key}: {weechat_log_data.value}"
    tail_msg = new_msg

    try:
        with open(filename, "r") as f:
            content = f.readlines()
    except FileNotFoundError:
        pass
    else:
        head = content[0]
        # last report timestamp in file
        pre_report_ts = re.findall(r"\d{1,2}:\d{1,2}", head)[0]
        pre_report_m_d = (head.split("reported at")[-1].split(
            pre_report_ts)[0].strip())
        date_flag = (pre_report_m_d == today_m_d)

        tail = content[-1].strip()
        tail_flag = tail.startswith("[") and tail.endswith("]")

        if date_flag and tail_flag:
            if "From gcalcli agenda" in head:
                pre_event_ts = re.findall(r"\d{1,2}:\d{1,2}", tail)
                pre_event = datetime.strptime(pre_event_ts[0], "%H:%M")
                allowed_event = (pre_event + timedelta(seconds=30)).time()
                allow_report_flag = (now_h_m > allowed_event)
            else:
                allow_report_flag = True

            if allow_report_flag:
                msg_list += content[1:-1]
                msg_list.append(f"{tail[1:-1]}\n")
            else:
                if weechat_log_data.header == "From gcalcli agenda":
                    return
                else:
                    msg_list = content[:-1]
                    msg_list.append(f"{tail_msg}\n")
                    tail_msg = tail[1:-1]

    os.popen(
        "tmux set display-time {0} && tmux display-message '{1}' &".format(
            5 * 1000, re.sub(' +', ' ', new_msg)
        )
    )

    msg_list.append(f"[{tail_msg}]")
    with open(filename, "w") as f:
        f.write("".join(msg_list))


def parse_today_event(filename="/tmp/gcalcli_agenda.txt"):
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    today_m_d = datetime.strptime(
        datetime.today().strftime("%a %b %d"), "%a %b %d")
    today_event_dict = {}
    today_flag = False

    try:
        with open(filename, "r") as r_fd:
            for line in r_fd:
                line_remove_colour = ansi_escape.sub("", line)
                date = " ".join(line_remove_colour.split()[:3])
                try:
                    m_d = datetime.strptime(date, "%a %b %d")
                except ValueError:
                    pass
                else:
                    if m_d == today_m_d:
                        today_flag = True
                    elif m_d > today_m_d:
                        return today_event_dict

                time_list = re.findall(r"\d{1,2}:\d{1,2}", line_remove_colour)
                if time_list:
                    time = time_list[-1].strip()
                    cal_list = line_remove_colour.split(time)
                    event = re.sub(" +", " ", cal_list[-1].strip())
                    if today_flag and time and event:
                        today_event_dict[time] = event
    except FileNotFoundError:
        pass
    return today_event_dict


def cron_timer_cb(data, remaining_calls):
    now_h_m = datetime.now().time()
    today_event_dict = parse_today_event()
    for key, value in today_event_dict.items():
        event_time = datetime.strptime(key, "%H:%M")
        reminder = (event_time - timedelta(minutes=10)).time()
        if now_h_m > reminder and now_h_m < event_time.time():
            update_weechat_log(WeechatLogData(key, value,
                                              "From gcalcli agenda"))
            return weechat.WEECHAT_RC_OK
    return weechat.WEECHAT_RC_OK

# Functions


def notify_show(data, signal, message):
    """Sends highlight message to be printed on notification"""

    if ((weechat.config_get_plugin('show_hilights') == "on"
         and signal == "weechat_pv")
            or (weechat.config_get_plugin('show_priv_msg') == "on"
                and signal == "weechat_highlight")):
        m = message.split("\t", 1)
        name = m[0].strip()
        msg = m[1].replace("'", "")[:64].strip()
        if name == "*":
            name = msg.split()[0]
        update_weechat_log(WeechatLogData(name, msg,
                                          f"{str(data)} from {name}"))
    elif (weechat.config_get_plugin('dele_msg_file') == "on"
            and signal == "input_text_changed"):
        delete_weechat_log()
    return weechat.WEECHAT_RC_OK

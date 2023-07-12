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
import string
import os
import re
from datetime import datetime, timedelta

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


gcalcli_mark = "From gcalcli agenda"


def update_weechat_log(msg, filename="/tmp/weechat_msg.txt", delete_en=False):
    update_file_flag = True
    display_msg = msg
    try:
        r_fd = open(filename, "r")
        content = r_fd.readlines()
        r_fd.close()

        head = content[0]
        tail = content[-1]
        tail_flag = "[" in tail and "]" in tail

        if delete_en:
            if tail_flag:
                msg = "".join(content[:-1])
                display_msg = ""
            else:
                update_file_flag = False
        else:
            if gcalcli_mark in msg:  # gcalcli message
                if gcalcli_mark in head:
                    # last message in file
                    pre_ts = re.findall(r"\d{1,2}:\d{1,2}", head)[0]
                    pre_report = datetime.strptime(pre_ts, "%H:%M")
                    allowed_report = (pre_report + timedelta(minutes=10)).time()
                    pre_m_d = (head.split("reported at")[-1]
                               .split(pre_ts)[0].strip())
                    today_m_d = datetime.today().strftime("%a %b %d")
                    pre_event_ts = re.findall(r"\d{1,2}:\d{1,2}", tail)
                    if tail_flag and pre_event_ts and pre_m_d == today_m_d:
                        pre_event = datetime.strptime(pre_event_ts[0], "%H:%M")
                    else:
                        pre_event = datetime.now()
                    allowed_event = (pre_event + timedelta(seconds=30)).time()
                    # current message
                    first_line = msg.split(os.linesep, 1)[0]
                    ts = re.findall(r"\d{1,2}:\d{1,2}", first_line)[0]
                    report = datetime.strptime(ts, "%H:%M").time()
                    if report < allowed_event and report < allowed_report:
                        update_file_flag = False
            else:  # normal weechat message
                if tail_flag:
                    update_file_flag = False
                else:
                    msg_list = msg.split("<--->", 1)
                    m = msg_list[-1].split("\t", 1)
                    name = m[0].strip()
                    message = m[1].replace("'", "")[:64].strip()
                    if name == "*":
                        name = message.split(max=1)[0]
                    display_msg = (f"{msg_list[0]}{message}\n"
                                   + f"    ---messge from: [{name}]")
                    msg = f"{head}" + f"{display_msg}"
    except:
        pass

    if update_file_flag:
        if display_msg.strip():
            os.popen("tmux set display-time {0} && tmux display-message '{1}' &"
                     .format(5 * 1000,
                         re.sub(' +', ' ',
                                display_msg.replace(os.linesep, " "))))
        with open(filename, "w") as f:
            f.write(f"{msg}")


def cron_timer_cb(data, remaining_calls):
    r_filename = "/tmp/gcalcli_agenda.txt"
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    today_m_d = datetime.today().strftime("%a %b %d")
    now_h_m = datetime.now().time()
    today_event_dict = {}
    today_flag = False
    if os.path.isfile(r_filename):
        with open(r_filename, "r") as r_fd:
            for line in r_fd:
                line_remove_colour = ansi_escape.sub("", line)
                try:
                    date = " ".join(line_remove_colour.split()[:3])
                    datetime.strptime(date, "%a %b %d")
                    if today_flag and date != today_m_d:
                        break
                    if date == today_m_d:
                        today_flag = True
                except ValueError:
                    pass
                time_list = re.findall(r"\d{1,2}:\d{1,2}", line_remove_colour)
                if not line_remove_colour.strip() or not time_list:
                    continue
                time = time_list[-1].strip()
                cal_list = line_remove_colour.split(time)
                event = re.sub(" +", " ", cal_list[-1].strip())
                if today_flag and time and event:
                    today_event_dict[time] = event
        for key, value in today_event_dict.items():
            event_time = datetime.strptime(key, "%H:%M")
            reminder = (event_time - timedelta(minutes=10)).time()
            if now_h_m > reminder and now_h_m < event_time.time():
                msg = (f'{gcalcli_mark}: reported at '
                       + f'{today_m_d} {now_h_m.strftime("%H:%M")}\n'
                       + f'    [{key} {value}]')
                update_weechat_log(msg)
                break
    return weechat.WEECHAT_RC_OK

# Functions


def notify_show(data, signal, message):
    """Sends highlight message to be printed on notification"""
    display_message_flag = False
    delete_flag = False

    if (weechat.config_get_plugin('show_hilights') == "on"
            and signal == "weechat_pv"):
        display_message_flag = True
    if (weechat.config_get_plugin('show_priv_msg') == "on"
            and signal == "weechat_highlight"):
        display_message_flag = True
    if (weechat.config_get_plugin('dele_msg_file') == "on"
            and signal == "input_text_changed"):
        display_message_flag = True
        delete_flag = True

    if display_message_flag:
        update_weechat_log(f"{str(data)}<--->{message}", delete_en=delete_flag)
    return weechat.WEECHAT_RC_OK

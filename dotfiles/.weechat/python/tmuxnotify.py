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

WEECHAT_LOG_FILENAME = "/tmp/weechat_msg.txt"
GCALCLI_LOG_FILENAME = "/tmp/gcalcli_agenda.txt"
FROM_GCALCLI, FROM_IRC = range(2)
GCALCLI_HEADER = "--- From gcalcli agenda, reported at: "
IRC_HEADER = "--- From irc message, reported at: "


@dataclass
class WeechatLogData:
    source: int  # reported from gcalcli or irc
    key: str     # timestamp for gcalcli, name for irc
    value: str   # event for gcalcli, message for irc
    header: str


def delete_weechat_log(report_source):
    try:
        with open(WEECHAT_LOG_FILENAME, "r") as f:
            content = f.read()
            content_list = content.splitlines()
    except FileNotFoundError:
        pass
    else:
        if report_source == FROM_GCALCLI:  # remove head
            if GCALCLI_HEADER in content:
                if IRC_HEADER in content:
                    content_list = content_list[4:]
                else:
                    content_list = content_list[2:]
            else:
                return True
        else:  # remove tail
            if IRC_HEADER in content:
                if GCALCLI_HEADER in content:
                    content_list = content_list[:2]
                else:
                    content_list = []
            else:
                return True

        with open(WEECHAT_LOG_FILENAME, "w") as f:
            f.write("\n".join(content_list) + "\n" if content_list else "")


def update_gcalcli_log(new_msg, content, today_m_d, now_h_m):
    head = content[0].strip()
    if head.startswith("<") and head.endswith(">"):
        pre_report_ts = re.findall(r"\d{1,2}:\d{1,2}", content[1])[-1]
        pre_report_m_d = (content[1].split("reported at: ")[-1].split(
            pre_report_ts)[0].strip())
        pre_event = datetime.strptime(pre_report_ts, "%H:%M")
        allowed_event = (pre_event + timedelta(seconds=30)).time()
        if pre_report_m_d == today_m_d and now_h_m < allowed_event:
            return None
        else:
            return f"{new_msg}{''.join(content[2:])}"
    else:
        return f"{new_msg}\n\n{''.join(content)}"


def update_irc_log(new_msg, content, today_m_d):
    tail = content[-1].strip()
    if tail.startswith("[") and tail.endswith("]"):
        pre_report_ts = re.findall(r"\d{1,2}:\d{1,2}", content[-2])[-1]
        pre_report_m_d = (content[-2].split("reported at: ")[-1].split(
            pre_report_ts)[0].strip())
        if pre_report_m_d == today_m_d:
            old_msg = re.sub(r'[\[\]]', "", "".join(content[-2:]))
            return f"{''.join(content[:-2])}{old_msg}{new_msg}"
        else:
            return f"{''.join(content)}{new_msg}"
    else:
        return f"{''.join(content)}\n\n{new_msg}"


def update_weechat_log(weechat_log_data):
    today_m_d = datetime.today().strftime("%a %b %d")
    now_h_m = datetime.now().time()
    new_msg = f"{weechat_log_data.key}: {weechat_log_data.value}"
    header = (
        f"{weechat_log_data.header}{today_m_d} {now_h_m.strftime('%H:%M')}"
    )

    if weechat_log_data.source == FROM_GCALCLI:
        out_msg = f"<{new_msg[:32]}>\n{header}\n"
    else:
        out_msg = f"{header}\n[{new_msg[:32]}]\n"

    try:
        with open(WEECHAT_LOG_FILENAME, "r") as f:
            content = f.readlines()
    except FileNotFoundError:
        pass
    else:
        if content:
            if weechat_log_data.source == FROM_GCALCLI:
                out_msg = update_gcalcli_log(
                    out_msg, content, today_m_d, now_h_m)
            else:
                out_msg = update_irc_log(out_msg, content, today_m_d)

    if out_msg:
        with open(WEECHAT_LOG_FILENAME, "w") as f:
            f.write(out_msg)

    os.popen(
        "tmux set display-time {0} && tmux display-message '{1}' &".format(
            5 * 1000, re.sub(' +', ' ', new_msg)
        )
    )


def parse_today_event():
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    today_w_m_d = datetime.today().strftime("%b %d")
    now_h_m = datetime.now().time()

    # before 8:00AM or after 8:00PM, it's out of work hour
    if now_h_m.hour < 8 or now_h_m.hour > 20:
        return None, None

    today_flag = False

    try:
        with open(GCALCLI_LOG_FILENAME, "r") as r_fd:
            for line in r_fd:
                line_remove_colour = ansi_escape.sub("", line)
                cur_date = " ".join(line_remove_colour.split()[:3])
                try:
                    w_m_d = datetime.strptime(
                        cur_date, "%a %b %d").strftime("%b %d")
                except ValueError:
                    pass
                else:
                    if w_m_d == today_w_m_d:
                        today_flag = True

                time_list = re.findall(r"\d{1,2}:\d{1,2}", line_remove_colour)
                if today_flag and time_list:
                    time = time_list[0].strip()
                    cal_list = line_remove_colour.split(time)
                    event = re.sub(" +", " ", cal_list[-1].strip())
                    event_time = datetime.strptime(time, "%H:%M")
                    reminder = (event_time - timedelta(minutes=10)).time()
                    if (time and event and now_h_m > reminder
                            and now_h_m < event_time.time()):
                        return time, event
    except FileNotFoundError:
        pass
    return None, None


def cron_timer_cb(data, remaining_calls):
    key, value = parse_today_event()
    if key and value:
        update_weechat_log(
            WeechatLogData(FROM_GCALCLI, key, value, GCALCLI_HEADER)
        )
    else:
        delete_weechat_log(FROM_GCALCLI)
    return weechat.WEECHAT_RC_OK


def get_ipv4():
    """get machine ipv4 address"""
    import socket
    if socket.gethostname() == "ct-lt-2215":
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ipv4_addr = s.getsockname()[0]
        s.close()
    else:
        ipv4_addr = "not target machine, bye"
    return ipv4_addr


def notify_show(data, signal, message):
    """Sends highlight message to be printed on notification"""

    if ((weechat.config_get_plugin('show_hilights') == "on"
         and signal == "weechat_highlight")
            or (weechat.config_get_plugin('show_priv_msg') == "on"
                and signal == "weechat_pv")):
        m = message.split("\t", 1)
        name = m[0].strip()
        msg = m[1].replace("'", "")[:64].strip()

        if (signal == "weechat_pv"
                and "haohu" in name.lower()
                and msg.lower().startswith("ip addr")):
            weechat.command("", f"/notice {name} localhost: {get_ipv4()}")
            return weechat.WEECHAT_RC_OK

        if name == "*":
            name = msg.split()[0]
        elif (name == "*status") or (name == "--" and msg.startswith("irc:")):
            return weechat.WEECHAT_RC_OK
        update_weechat_log(WeechatLogData(FROM_IRC, name, msg, IRC_HEADER))
    elif (weechat.config_get_plugin('dele_msg_file') == "on"
            and signal == "input_text_changed"):
        delete_weechat_log(FROM_IRC)
    return weechat.WEECHAT_RC_OK

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from collections import OrderedDict
import sys
import re

ALL_DAY_EVENT_KEY = "all_day_event_by_gcalcli"
# https://stackoverflow.com/a/28938235
COLOUR_OFF = '\033[0m'
COLOUR_BG_BLUE = '\033[44m'
COLOUR_BG_YELLOW = '\033[43m'
COLOUR_GREEN = '\033[0;32m'
COLOUR_PURPLE = '\033[0;35m'
COLOUR_LIGHT_GRAY = '\033[0;37m'


def to_colour(event_dict: OrderedDict) -> str:
    now_h_m = datetime.now().time()
    colour_event = (
        f"{COLOUR_BG_BLUE}"
        f"{datetime.today().strftime('%a %b %d')}"
        f"{COLOUR_OFF}\n"
    )

    for time, event in event_dict.items():
        if time == ALL_DAY_EVENT_KEY:
            for cur_event in event:
                colour_event += (
                    f"    {COLOUR_PURPLE}"
                    f"{cur_event}{COLOUR_OFF}\n"
                )
        else:
            event_time = datetime.strptime(time, "%H:%M")
            reminder_s = (event_time - timedelta(minutes=10)).time()
            reminder_e = (event_time + timedelta(minutes=5)).time()
            if now_h_m > reminder_s and now_h_m < reminder_e:
                colour_event += (
                    f"{COLOUR_BG_YELLOW}"
                    f"[*] {time}  {event}"
                    f"{COLOUR_OFF}\n"
                )
            elif now_h_m > reminder_e:
                colour_event += (
                    f"{COLOUR_LIGHT_GRAY}"
                    f"    {time}  {event}"
                    f"{COLOUR_OFF}\n"
                )
            else:
                colour_event += f"    {time}  {event}\n"
    return colour_event


def hyperlinks_text(url, hyper_txt):
    hyperlinks = '\033]8;{};{}\033\\{}\033]8;;\033\\'
    return hyperlinks.format("", url, hyper_txt)


def get_event(line, pre_item):
    time_list = re.findall(r"\d{1,2}:\d{1,2}", line)
    if time_list:
        time = time_list[0].strip()
        cal_list = line.split(time)
        event = re.sub(" +", " ", cal_list[-1].strip())
        return time, event

    pre_key, pre_val = pre_item
    if pre_key == ALL_DAY_EVENT_KEY:
        if line and line not in ["Home", "Office"] and not line.startswith(
                ("Location:", "Link:", "Hangout Link:")
        ):
            return ALL_DAY_EVENT_KEY, pre_val.append(f"{line} (All day)")
    else:
        if line.startswith("Location:"):
            location = line.split("Location:")[-1].strip()
            meeting_room = re.compile(
                r'\(Meeting Room\)-Dale House-(.+?) \(').findall(location)
            if meeting_room:
                location = meeting_room[0]
            pre_val_list = pre_val.splitlines()
            pre_val_list[0] = f"{pre_val_list[0]} ({location})"
            return pre_key, "\n".join(pre_val_list)
        elif line.startswith("Hangout Link:"):
            google_meet_url = line.split("Hangout Link:")[-1].strip()
            event_with_url = (f"{pre_val}\n{' ' * 10}"
                              f"{COLOUR_GREEN}<{google_meet_url}>{COLOUR_OFF}")
            return pre_key, event_with_url
    return None, None


def parse_today_event(cal_log: str) -> OrderedDict:
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    today_w_m_d = datetime.today().strftime("%b %d")
    today_event_dict = OrderedDict()
    today_event_dict[ALL_DAY_EVENT_KEY] = []
    today_flag = False

    for line in cal_log.splitlines():
        line = ansi_escape.sub("", line).strip()
        cur_date = " ".join(line.split()[:3])
        try:
            w_m_d = datetime.strptime(
                cur_date, "%a %b %d").strftime("%b %d")
        except ValueError:
            pass
        else:
            if w_m_d == today_w_m_d:
                today_flag = True
                line = line.split(w_m_d)[-1].strip()
            else:
                if today_flag:
                    return today_event_dict

        key, value = get_event(line, list(today_event_dict.items())[-1])
        if key and value:
            today_event_dict[key] = value

    return today_event_dict


if __name__ == "__main__":
    event_dict = parse_today_event(sys.stdin.read())
    # sys.stdout.write(to_colour(event_dict))
    print(to_colour(event_dict))

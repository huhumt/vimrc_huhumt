#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from collections import OrderedDict
import subprocess
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
            for key, val in event.items():
                if key and val:
                    colour_event += (
                        f"    {COLOUR_PURPLE}"
                        f"{key} {val}{COLOUR_OFF}\n"
                    )
        else:
            event_time = datetime.strptime(time, "%H:%M")
            reminder_s = (event_time - timedelta(minutes=15)).time()
            reminder_e = (event_time + timedelta(minutes=5)).time()

            location = event.get("location", "")
            hangout = event.get("hangout", "")
            description_url = " ".join(event.get("description_url", []))

            if now_h_m > reminder_s and now_h_m < reminder_e:
                colour_event += (
                    f"{COLOUR_BG_YELLOW}"
                    + f"[*] {time}  {event['name']}"
                    + (f" {location}" if location else "")
                    + f"{COLOUR_GREEN}"
                    + (f"\n    [{description_url}]" if description_url else "")
                    + (f"\n    {hangout}" if hangout else "")
                    + f"{COLOUR_OFF}\n"
                )
            elif now_h_m > reminder_e:
                colour_event += (
                    f"{COLOUR_LIGHT_GRAY}"
                    + f"    {time}  {event['name']}"
                    + (f" {location}" if location else "")
                    + f"{COLOUR_OFF}\n"
                )
            else:
                colour_event += (
                    f"    {time}  {event['name']}"
                    + (f" {location}" if location else "")
                    + f"{COLOUR_OFF}\n"
                )
    return colour_event


def hyperlinks_text(url, hyper_txt):
    hyperlinks = '\033]8;{};{}\033\\{}\033]8;;\033\\'
    return hyperlinks.format("", url, hyper_txt)


def get_event(line, pre_line):
    if line.startswith("Link:"):
        time_list = re.findall(r"^\d{1,2}:\d{2} ", pre_line)
        if time_list:
            time = time_list[0].strip()
            event = re.sub(" +", " ", pre_line.split(time, 1)[-1].strip())
            return time, "name", event
        else:
            if pre_line not in ("Home", "Office"):
                return ALL_DAY_EVENT_KEY, pre_line, "(All day)"
    elif line.startswith("Location:"):
        location = line.split("Location:", 1)[-1].strip()
        meeting_room = re.compile(
            r'\(Meeting Room\)-Dale House-(.+?) \(').findall(location)
        return None, "location", f"({meeting_room[0] if meeting_room else location})"
    elif line.startswith("Hangout Link:"):
        return None, "hangout", f"<{line.split('Hangout Link:', 1)[-1].strip()}>"
    return None, None, None


def parse_today_event(cal_log: str) -> None | OrderedDict:
    today_w_m_d = datetime.today().strftime("%a %b %d")
    today_log_list = re.compile(
        fr"{today_w_m_d}.*(?:\r?\n(?!\r?\n).*)*"
    ).findall(cal_log)

    if not today_log_list:
        return None

    today_log = today_log_list[0]
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    event_dict = OrderedDict()

    pre_line = None
    event_time = None

    for line in today_log.splitlines():
        line = ansi_escape.sub("", line).split(today_w_m_d)[-1].strip()
        time, key, value = get_event(line, pre_line)
        if key and value:
            if time:
                event_time = time
                event_dict[time] = {key: value}
            else:
                event_dict[event_time][key] = value
        pre_line = line

        if line == "Description:":
            description_url_list = []
            for href in re.compile(
                fr'{event_time}[\s\S]+?<a href="(?P<url>[\s\S]+?)">'
            ).findall(today_log):
                description_url = "".join(
                    [s for s in href.split() if not s.startswith('\x1b')]
                )
                short_url = subprocess.run(
                    [
                        'shorten_url',
                        "--url-min-length=16",
                        description_url
                    ],
                    stdout=subprocess.PIPE
                ).stdout.decode('utf-8').strip()
                description_url_list.append(short_url)
            if description_url_list:
                event_dict[event_time]["description_url"] = description_url_list

    return event_dict


if __name__ == "__main__":
    event_dict = parse_today_event(sys.stdin.buffer.read().decode('utf-8', 'ignore'))
    if event_dict:
        print(to_colour(event_dict))

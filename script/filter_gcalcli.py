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

    for event_name in event_dict:
        event_time = event_dict[event_name]["time"]
        event_attr = event_dict[event_name]["attr"]

        if event_time == ALL_DAY_EVENT_KEY:
            colour_event += (
                f"    {COLOUR_PURPLE}"
                f"{event_name} (All Day){COLOUR_OFF}\n"
            )
        else:
            reminder_c = datetime.strptime(event_time, "%H:%M")
            reminder_s = (reminder_c - timedelta(minutes=15)).time()
            reminder_e = (reminder_c + timedelta(minutes=5)).time()

            location = event_attr.get("location", "")
            hangout = event_attr.get("hangout", "")
            description_url = " ".join(event_attr.get("description_url", []))
            display_list = list(
                filter(None, [location, hangout, description_url]))

            if now_h_m > reminder_s and now_h_m < reminder_e:
                colour_event_dict = {
                    COLOUR_BG_YELLOW: (
                        f"[*] {event_time}  {event_name}"
                        + (f" ({display_list[0]})" if display_list else "")
                    ),
                    COLOUR_GREEN: "".join(
                        [f'\n    {s}'
                         for s in display_list[1:] if len(display_list) > 1]
                    )
                }
            elif now_h_m > reminder_e:
                colour_event_dict = {
                    COLOUR_LIGHT_GRAY: (
                        f"    {event_time}  {event_name}"
                        + (f" ({display_list[0]})" if display_list else "")
                    )
                }
            else:
                colour_event_dict = {
                    COLOUR_OFF: (
                        f"    {event_time}  {event_name}"
                        + (f" ({display_list[0]})" if display_list else "")
                    )
                }

            for colour, event in colour_event_dict.items():
                colour_event += f"{colour}{event}"
            colour_event += f"{COLOUR_OFF}\n"

    return colour_event


def hyperlinks_text(url, hyper_txt):
    hyperlinks = '\033]8;{};{}\033\\{}\033]8;;\033\\'
    return hyperlinks.format("", url, hyper_txt)


def get_event(line, pre_line, event_name, today_log):
    if line.startswith("Link:"):
        time_list = re.findall(r"^\d{1,2}:\d{2} ", pre_line)
        if time_list:
            time = time_list[0].strip()
            event = re.sub(" +", " ", pre_line.split(time, 1)[-1].strip())
            return time, "event", event
        else:
            if pre_line not in ("Home", "Office"):
                return ALL_DAY_EVENT_KEY, "(All day)", pre_line
    elif line.startswith("Location:"):
        location = line.split("Location:", 1)[-1].strip()
        meeting_room = re.compile(
            r'\(Meeting Room\)-Dale House-(.+?) \(').findall(location)
        return None, "location", f"{meeting_room[0] if meeting_room else location}"
    elif line.startswith("Hangout Link:"):
        return None, "hangout", f"{line.split('Hangout Link:', 1)[-1].strip()}"
    elif line.startswith("Description:"):
        description_url_list = []
        for href in re.compile(
            fr'{event_name}[\s\S]+?<a href="(?P<url>[\s\S]+?)">'
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
            return None, "description_url", description_url_list
    return None, None, None


def parse_today_event(cal_log: str) -> OrderedDict:
    today_w_m_d = datetime.today().strftime("%a %b %d")
    today_log_list = re.compile(
        fr"{today_w_m_d}.*(?:\r?\n(?!\r?\n).*)*"
    ).findall(cal_log)

    if not today_log_list:
        if datetime.today().isoweekday() > 5:
            holiday_event = "Weekends"
        else:
            holiday_event = "On holiday"

        return OrderedDict({
            holiday_event: {
                "time": ALL_DAY_EVENT_KEY,
                "attr": {}
            }
        })

    today_log = today_log_list[0]
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    event_dict = OrderedDict()
    pre_line = None
    event_name = None

    for line in today_log.splitlines():
        line = ansi_escape.sub("", line).split(today_w_m_d)[-1].strip()
        time, key, value = get_event(line, pre_line, event_name, today_log)
        pre_line = line

        if key and value:
            if time:
                event_name = value
                event_dict[event_name] = {"time": time, "attr": {}}
            else:
                event_dict[event_name]["attr"][key] = value
    return event_dict


if __name__ == "__main__":
    event_dict = parse_today_event(
        sys.stdin.buffer.read().decode('utf-8', 'ignore'))
    if event_dict:
        print(to_colour(event_dict))

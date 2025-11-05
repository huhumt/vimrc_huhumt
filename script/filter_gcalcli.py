#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
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


def to_colour(m_w_d: str, event_list: list, tomorrow_flag: bool) -> str:
    now_h_m = datetime.now().time()
    colour_header = f"{COLOUR_BG_BLUE}{m_w_d}{COLOUR_OFF}\n"
    colour_event = str()

    for event in event_list:
        event_time = event.get("time")
        event_name = event.get("event")

        if event_time == ALL_DAY_EVENT_KEY:
            colour_event = (
                f"    {COLOUR_PURPLE}"
                f"{event_name} (All Day){COLOUR_OFF}\n"
            ) + colour_event
        else:
            display_list = list(filter(None, [
                event.get("location"),
                event.get("hangout"),
                event.get("description_url")
            ]))

            if tomorrow_flag:
                in_event_flag = False
                done_event_flag = False
            else:
                reminder_c = datetime.strptime(event_time, "%H:%M")
                reminder_s = (reminder_c - timedelta(minutes=15)).time()
                reminder_e = (reminder_c + timedelta(minutes=5)).time()
                in_event_flag = now_h_m > reminder_s and now_h_m < reminder_e
                done_event_flag = now_h_m > reminder_e

            if in_event_flag:
                colour_event_list = {
                    COLOUR_BG_YELLOW: (
                        f"[*] {event_time}  {event_name}"
                        + (f" ({display_list[0]})" if display_list else "")
                    ),
                    COLOUR_GREEN: "".join(
                        [f'\n    {s}'
                         for s in display_list[1:] if len(display_list) > 1]
                    )
                }
            elif done_event_flag:
                colour_event_list = {
                    COLOUR_LIGHT_GRAY: (
                        f"    {event_time}  {event_name}"
                        + (f" ({display_list[0]})" if display_list else "")
                    )
                }
            else:
                colour_event_list = {
                    COLOUR_OFF: (
                        f"    {event_time}  {event_name}"
                        + (f" ({display_list[0]})" if display_list else "")
                    )
                }

            for colour, event in colour_event_list.items():
                colour_event += f"{colour}{event}"
            colour_event += f"{COLOUR_OFF}\n"

    return f"{colour_header}{colour_event}"


def hyperlinks_text(url: str, hyper_txt: str) -> str:
    hyperlinks = '\033]8;{};{}\033\\{}\033]8;;\033\\'
    return hyperlinks.format("", url, hyper_txt)


def search_and_short_url(urls: str) -> list:
    url_list = list()
    for href in re.compile(r'<a href="(?P<url>[^"]+)"').findall(urls):
        url_list.append(subprocess.run([
            'shorten_url',
            "--url-min-length=16",
            re.sub(r'[\s\|]', '', href)
        ], stdout=subprocess.PIPE).stdout.decode('utf-8').strip())
    return url_list


def update_event_list(date_log: str, event_list: list) -> None:
    re_event = re.compile(
        r'\s+(?P<time>\d{1,2}:\d{2})?\s*(?P<event>.*)'
        r'(?:\s+Link: (?P<link>.+))?'
        r'(?:\s+Hangout Link: (?P<hangout_link>.+))?'
        r'(?:\s+Location: (?P<location>.+))?'
        r'(?:\s+Description:[-+\s]+(?P<description>[^+]+)[-+]+)?'
    )
    for (
        time, event, link, hangout_link, location, description
    ) in re_event.findall(date_log):
        meeting_room = re.compile(
            r'\(Meeting Room\)-Dale House-(.+?) \(').findall(location)
        if event and event.lower() not in ("home", "office"):
            if re.compile(r'\| Public holiday[ ]+\|').search(description):
                event = f"Public holiday: {event}"
            event_list.append({
                "time": time if time else ALL_DAY_EVENT_KEY,
                "event": event,
                "link": link,
                "hangout_link": hangout_link,
                "location": meeting_room[0] if meeting_room else location,
                "description_url": " ".join(search_and_short_url(description))
            })


def remove_colour(input_str: str) -> str:
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", input_str)


def parse_event(cal_log: str, tomorrow_flag: bool) -> tuple[str, list]:
    w_m_d = (datetime.today() + timedelta(days=tomorrow_flag)
             ).strftime("%a %b %d")
    re_date = fr"(?:{w_m_d})(?P<date_log>.*(?:\r?\n(?!\r?\n).*)*)"

    event_list = list()
    # temporary code, delete when ready
    event_list.append({"time": "15:00", "event": "Pick up school"})

    if log_list := re.findall(re_date, cal_log):
        update_event_list(log_list[0], event_list)
    else:
        if datetime.today().isoweekday() > 5:
            event_list += [{"time": ALL_DAY_EVENT_KEY, "event": "Weekends"}]
        else:
            event_list += [{"time": ALL_DAY_EVENT_KEY, "event": "On holiday"}]

    return w_m_d, event_list


def read_from_file(filename: str, tomorrow_flag: bool) -> dict | None:
    a_day_ago = (datetime.today() - timedelta(days=1-tomorrow_flag)
                 ).strftime("%a %b %d")
    re_holiday = r'(?P<holiday>.*holiday)[ ]*\((?P<duration>\d+)[ ]*day[s]?\)'
    try:
        with open(filename, "r") as f:
            content = remove_colour(f.read())
            if holiday := re.findall(re_holiday, content, re.IGNORECASE)[0]:
                name = holiday[0].strip()
                day = int(holiday[1].strip())

                # can only be yesterday or today
                if name and (left_day := day - int(a_day_ago in content)) > 0:
                    day_label = 'days' if left_day > 1 else 'day'
                    return {
                        "time": ALL_DAY_EVENT_KEY,
                        "event": f"{name} ({left_day} {day_label})"
                    }
    except FileNotFoundError:
        return None
    except IndexError:
        return None


if __name__ == "__main__":
    # display tomorrow event after 17:00
    tomorrow_flag = datetime.now().hour > 16
    w_m_d, event_list = parse_event(remove_colour(
        sys.stdin.buffer.read().decode('utf-8', 'ignore')), tomorrow_flag)
    if holiday := read_from_file("/tmp/gcalcli_agenda.txt", tomorrow_flag):
        event_list.append(holiday)
    if event_list:
        print(to_colour(w_m_d, event_list, tomorrow_flag))

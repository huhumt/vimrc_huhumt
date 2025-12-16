#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from collections import OrderedDict
import subprocess
import argparse
import json
import sys
import re

ALL_DAY_EVENT_KEY = "00:00"
# https://stackoverflow.com/a/28938235
COLOUR_OFF = '\033[0m'
COLOUR_BG_BLUE = '\033[44m'
COLOUR_BG_YELLOW = '\033[43m'
COLOUR_GREEN = '\033[0;32m'
COLOUR_PURPLE = '\033[0;35m'
COLOUR_LIGHT_GRAY = '\033[0;37m'
GCALCLI_FILENAME = "/tmp/gcalcli_agenda.json"


def to_colour(w_m_d: str, event_list: list, days_later: int) -> str:
    colour_off_flag = days_later > 0
    now_h_m = datetime.now().time()
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
                event.get("hangout_link"),
                event.get("description_url")
            ]))

            if colour_off_flag:
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

    if colour_off_flag:
        d_flag = f"{days_later} days later" if days_later > 1 else "tomorrow"
        colour_header = f"{COLOUR_BG_BLUE}{w_m_d} ({d_flag}){COLOUR_OFF}\n"
    else:
        colour_header = f"{COLOUR_BG_BLUE}{w_m_d}{COLOUR_OFF}\n"

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


def update_event_dict(date_log: str) -> OrderedDict:
    re_week = 'Mon|Tue|Wed|Thu|Fri|Sat|Sun'
    re_month = 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec'
    re_event = re.compile(
        fr'(?P<date>(?:{re_week}) (?:{re_month}) \d+)?'
        r'[ ]+(?P<time>\d{1,2}:\d{2})?[ ]*(?P<event>.+)'
        r'(?:\s+Link: (?P<link>.+))?'
        r'(?:\s+Hangout Link: (?P<hangout_link>.+))?'
        r'(?:\s+Location: (?P<location>.+))?'
        r'(?:\s+Description:[-+\s]+(?P<description>[^+]+)[-+]+)?'
    )

    cur_date = None
    cur_date_list = []
    event_dict = OrderedDict()

    for (
        date, time, event, link, hangout_link, location, description
    ) in re_event.findall(date_log):
        meeting_room = re.compile(
            r'\(Meeting Room\)-Dale House-(.+?) \(').findall(location)
        # do not record if event in empty
        # do not record event in "home" or "office"
        # do not record regional holiday not valid in England
        # do not record duplicated event
        event_lower = event.lower().strip()
        if (not event_lower) or event_lower in ("home", "office") or (
            "(regional holiday)" in event_lower and "England" not in location
        ) or event_lower in cur_date_list:
            cur_event = None
        else:
            attr = re.compile(
                r'\| (?P<attr>Public holiday|Observance)[ ]+\|'
            ).findall(description)
            cur_event = {
                "time": time if time else ALL_DAY_EVENT_KEY,
                "event": (f"{attr[0]}: " if attr else "") + event,
                "link": link,
                "hangout_link": hangout_link,
                "location": meeting_room[0] if meeting_room else location,
                "description_url": " ".join(search_and_short_url(description))
            }
        if date:
            cur_date = date
            cur_date_list = [event_lower]
            event_dict.update({date: [cur_event] if cur_event else []})
        else:
            cur_date_list.append(event_lower)
            if cur_date and cur_event:
                event_dict[cur_date].append(cur_event)
    return event_dict


def remove_colour(input_str: str) -> str:
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", input_str).strip()


def read_from_file(w_m_d: str, new_w_m_d: str, days_later: int) -> tuple[bool, dict] | None:
    try:
        with open(GCALCLI_FILENAME,
                  "r", encoding="utf-8", errors="ignore") as f:
            holiday_dict: OrderedDict = json.load(f)
    except FileNotFoundError:
        return None

    for today_event_dict in holiday_dict.get(w_m_d, []):
        event = today_event_dict.get("event")
        if holiday := re.findall(
                r'(?P<name>.*holiday.*)\((?P<duration>\d+) day[s]*\)',
                event, re.IGNORECASE):
            name = holiday[0][0]
            duration = int(holiday[0][1].strip())

            if (left_day := duration - days_later) > 0:
                day_label = 'days' if left_day > 1 else 'day'
                today_event_dict.update({
                    "event": f"{name}({left_day} {day_label})"
                })
                return (today_event_dict in holiday_dict.get(new_w_m_d, []),
                        today_event_dict)


def to_date(from_date: datetime) -> str:
    return from_date.strftime("%a %b %d")


def main_out_agenda(event_dict: dict, to_file: bool) -> None:
    today_date = datetime.today()
    week_num = today_date.isoweekday()
    if (week_num > 5) or (week_num == 5 and today_date.hour > 16):
        # display next Monday's event from Friday's afternoon
        days_later = 8 - week_num
    else:
        # display tomorrow event after 17:00
        days_later = 1 if today_date.hour > 16 else 0

    event_date = today_date + timedelta(days=days_later)
    w_m_d = to_date(event_date)

    if w_m_d in event_dict:
        event_list = event_dict.get(w_m_d, [])
    else:
        event_list = [{
            "time": ALL_DAY_EVENT_KEY,
            "event": "Weekends" if event_date.isoweekday() > 5 else "On holiday"
        }]

    if to_file and (holiday := read_from_file(
            to_date(today_date), to_date(event_date), days_later)):
        holiday_exist_flag, holiday_dict = holiday
        event_list.append(holiday_dict)
        to_file &= (not holiday_exist_flag)

    event_list.sort(key=lambda x: int(x["time"].replace(":", "")))
    if event_list:
        print(to_colour(w_m_d, event_list, days_later))

    if to_file:
        with open(GCALCLI_FILENAME, "w", encoding="utf-8") as f:
            json.dump(event_dict, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Filter gcalcli agenda message")
    parser.add_argument(
        "--out-event-only", dest="out_event_only", action="store_true",
        help="Output coloured agenda message")
    parser.add_argument(
        "--from-file", dest="from_file", action="store_true", default=False,
        help="Read agenda message from file GCALCLI_FILENAME")
    parser.add_argument(
        "--to-file", dest="to_file", action="store_true", default=True,
        help="Save agenda message to file GCALCLI_FILENAME")

    args = parser.parse_args()

    if args.from_file:
        try:
            with open(GCALCLI_FILENAME,
                      "r", encoding="utf-8", errors="ignore") as f:
                event_dict = json.load(f)
                args.to_file = False  # do not write to file if read from file
        except FileNotFoundError:
            exit()
    else:
        event_dict = update_event_dict(remove_colour(
            sys.stdin.buffer.read().decode('utf-8', 'ignore')))

    if args.out_event_only:
        for today_event in event_dict.get(to_date(datetime.today()), []):
            event_time = today_event.get("time")
            event_time = "" if event_time == ALL_DAY_EVENT_KEY else event_time
            event = today_event.get("event")
            print(f"{event_time}    {event}")
    else:
        main_out_agenda(event_dict, args.to_file)

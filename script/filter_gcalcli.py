#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import subprocess
import argparse
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


def update_event_dict(date_log: str) -> dict:
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
    event_dict = dict()

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


def read_from_file(filename: str, week_num: int) -> dict | None:
    re_week_num = r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun) '
    re_holiday = r'(?P<holiday>.*holiday)[ ]*\((?P<duration>\d+)[ ]*day[s]?\)'
    weekday_to_num_dict = {
        "Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5, "Sat": 6, "Sun": 7
    }
    try:
        with open(filename, "r") as f:
            content = remove_colour(f.read())
            if ((holiday := re.findall(re_holiday, content, re.IGNORECASE))
                    and (old_week := re.findall(re_week_num, content))):
                name = holiday[0][0].strip()
                day = int(holiday[0][1].strip())
                old_week_num = weekday_to_num_dict.get(old_week[0], week_num)

                if (delta_days := week_num - old_week_num) < 0:
                    delta_days += 7

                if name and (left_day := day - delta_days) > 0:
                    day_label = 'days' if left_day > 1 else 'day'
                    return {
                        "time": ALL_DAY_EVENT_KEY,
                        "event": f"{name} ({left_day} {day_label})"
                    }
    except FileNotFoundError:
        return None


def main_out_agenda(event_dict: dict) -> None:
    today_date = datetime.today()
    week_num = today_date.isoweekday()
    if (week_num > 5) or (week_num == 5 and today_date.hour > 16):
        # display next Monday's event from Friday's afternoon
        days_later = 8 - week_num
    else:
        # display tomorrow event after 17:00
        days_later = 1 if today_date.hour > 16 else 0

    event_date = datetime.today() + timedelta(days=days_later)
    w_m_d = event_date.strftime("%a %b %d")

    if w_m_d in event_dict:
        event_list = event_dict.get(w_m_d, [])
    else:
        event_list = [{
            "time": ALL_DAY_EVENT_KEY,
            "event": "Weekends" if event_date.isoweekday() > 5 else "On holiday"
        }]

    new_week_num = (today_date + timedelta(days=days_later)).isoweekday()
    if holiday := read_from_file("/tmp/gcalcli_agenda.txt", new_week_num):
        event_list.append(holiday)
    if event_list:
        print(to_colour(
            w_m_d,
            sorted(event_list, key=lambda x: int(x["time"].replace(":", ""))),
            days_later
        ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Filter gcalcli agenda message")
    parser.add_argument(
        "--out-event-only", dest="out_event_only", action="store_true",
        help="Output coloured agenda message")

    args = parser.parse_args()
    agenda = remove_colour(sys.stdin.buffer.read().decode('utf-8', 'ignore'))
    event_dict = update_event_dict(agenda)
    if args.out_event_only:
        for key, event_list in event_dict.items():
            for event in event_list:
                print("|".join([key, event.get("time"), event.get("event")]))
    else:
        main_out_agenda(event_dict)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from collections import OrderedDict
import subprocess
import argparse
import json
import sys
import re

ALL_DAY_EVENT_KEY = "All day event"
# https://stackoverflow.com/a/28938235
COLOUR_OFF = '\033[0m'
COLOUR_BG_BLUE = '\033[44m'
COLOUR_BG_YELLOW = '\033[43m'
COLOUR_GREEN = '\033[0;32m'
COLOUR_PURPLE = '\033[0;35m'
COLOUR_LIGHT_GRAY = '\033[0;37m'
HEADER_COLOUR = COLOUR_BG_BLUE + "{header}" + COLOUR_OFF
ALL_DAY_COLOUR = "    " + COLOUR_PURPLE + "{name} (All Day)" + COLOUR_OFF
NORMAL_EVENT_COLOUR = "    {event}"
DONE_EVENT_COLOUR = "    " + COLOUR_LIGHT_GRAY + "{event}" + COLOUR_OFF
IN_EVENT_COLOUR = (COLOUR_BG_YELLOW + "[*] {event}"
                   + COLOUR_GREEN + "{url}" + COLOUR_OFF)


def to_colour(header: str, event_list: list, colour_en: bool) -> str:
    now_h_m = datetime.now().time()
    event_name_list = list()
    colour_out_str = HEADER_COLOUR.format(header=header)

    for event in event_list:
        event_time = event.get("time")
        event_name = event.get("event")

        if event_name not in event_name_list:
            event_name_list.append(event_name)
            if event_time == ALL_DAY_EVENT_KEY:
                colour_str = ALL_DAY_COLOUR.format(name=event_name)
            else:
                event_loc = re.sub(
                    r'(.+)', r' (\1)', event.get("location").strip())
                event_url = '\n    ' + '\n    '.join(list(filter(None, [
                    event.get("hangout_link"), event.get("description_url")])))
                cur_event = f"{event_time}  {event_name}{event_loc}"

                reminder_c = datetime.strptime(event_time, "%H:%M")
                reminder_s = (reminder_c - timedelta(minutes=15)).time()
                reminder_e = (reminder_c + timedelta(minutes=5)).time()
                # colour disabled or event not start yet
                if (not colour_en) or (now_h_m < reminder_s):
                    colour_str = NORMAL_EVENT_COLOUR.format(event=cur_event)
                elif now_h_m > reminder_e:  # colour enabled and event finished
                    colour_str = DONE_EVENT_COLOUR.format(event=cur_event)
                else:  # colour enabled and now in the event
                    colour_str = IN_EVENT_COLOUR.format(
                        event=cur_event, url=event_url)
            colour_out_str += f"\n{colour_str}"
    return colour_out_str


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
    re_week = '(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)'
    re_month = '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
    re_event = re.compile(
        fr'(?P<date>(?:{re_week} {re_month} |\d+-\d+-)\d+)?'
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
        if date and (date != cur_date):
            cur_date_list = [event_lower]
            cur_date = date
        else:
            cur_date_list.append(event_lower)

        if date and (date not in event_dict):
            event_dict.update({date: [cur_event] if cur_event else []})
        else:
            if cur_date and cur_event:
                event_dict[cur_date].append(cur_event)
    return event_dict


def remove_colour(input_str: str) -> str:
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", input_str).strip()


def update_from_file(event_dict, days_later: int) -> dict | None:
    for today_event_dict in event_dict:
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
                return today_event_dict


def detect_date_format(date_str: str) -> str | None:
    # current only support these two formats
    #  "%a %b %d" is from 'gcalcli agenda'
    #  "%Y-%m-%d" is from 'gcalcli search'
    date_format_list = ["%a %b %d", "%Y-%m-%d"]
    for date_format in date_format_list:
        try:
            datetime.strptime(date_str, date_format)
        except ValueError:
            pass
        else:
            return date_format
    print(f"{date_str} is not support, can not continue")
    return None


def to_date(from_date: datetime, date_format: str) -> str:
    return from_date.strftime(date_format)


def main_out_agenda(event_dict, file_dict, date_format, days_later) -> None:
    today_date = datetime.today()

    if days_later < 0:
        week_num = today_date.isoweekday()
        if (week_num > 5) or (week_num == 5 and today_date.hour > 16):
            # display next Monday's event from Friday's afternoon
            days_later = 8 - week_num
        else:
            # display tomorrow event after 17:00
            days_later = 1 if today_date.hour > 16 else 0

    event_date = today_date + timedelta(days=days_later)
    w_m_d = to_date(event_date, date_format)
    # this is a pointer to event_dict, if key w_m_d:
    #   * in dict, any modification on this pointer will be auto saved to dict
    #   * not in dict, null pointer, work as local variable, won't update dict
    event_list = event_dict.get(w_m_d, []) or [{
        "time": ALL_DAY_EVENT_KEY,
        "event": "Weekends" if event_date.isoweekday() > 5 else "No Event found"
    }]

    if file_dict and (holiday := update_from_file(
            file_dict.get(to_date(today_date, date_format), []), days_later)):
        if holiday not in event_list:
            event_list.append(holiday)

    event_list.sort(
        key=lambda x: int(re.sub(r'(\d+)?:?(\d+)?.*', r'\1\2', x["time"]) or 0)
    )
    header_list = ["", " (tomorrow)", f" ({days_later} days later)"]
    header = header_list[days_later if days_later < len(header_list) else -1]
    print(to_colour(f"{w_m_d}{header}", event_list, days_later == 0))


if __name__ == "__main__":
    GCALCLI_FILENAME = "/tmp/gcalcli_agenda.json"

    parser = argparse.ArgumentParser(
        description="Filter gcalcli agenda message")
    parser.add_argument(
        "--out-event-only", dest="out_event_only", action="store_true",
        help="Output today's event only")
    parser.add_argument(
        "--from-file", dest="from_file", action="store_true", default=False,
        help=f"Read agenda message from file GCALCLI_FILENAME")
    parser.add_argument(
        "--days-later", dest="days_later", type=int, default=-1,
        help="Display n days later agenda, must be within 30 days")

    args = parser.parse_args()

    try:
        with open(GCALCLI_FILENAME,
                  "r", encoding="utf-8", errors="ignore") as f:
            from_file_event_dict = json.load(f)
    except FileNotFoundError:
        from_file_event_dict = None

    if args.from_file or sys.stdin.isatty():
        if from_file_event_dict:
            event_dict = from_file_event_dict
        else:
            exit()
    else:
        event_dict = update_event_dict(remove_colour(
            sys.stdin.buffer.read().decode('utf-8', 'ignore')))

    if not (date_format := detect_date_format(list(event_dict.keys())[0])):
        raise ValueError(f"Invalid input data {event_dict}")

    if args.out_event_only:
        today_key = to_date(datetime.today(), date_format)
        for today_event in event_dict.get(today_key, []):
            event_time = today_event.get("time")
            event_time = "" if event_time == ALL_DAY_EVENT_KEY else event_time
            event = today_event.get("event")
            print(f"{event_time}    {event}")
    else:
        main_out_agenda(event_dict, from_file_event_dict,
                        date_format, args.days_later)
        if event_dict != from_file_event_dict:  # do not update if no changes
            with open(GCALCLI_FILENAME, "w", encoding="utf-8") as f:
                json.dump(event_dict, f, indent=4)

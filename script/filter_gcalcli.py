#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from collections import OrderedDict
from pathlib import Path
import subprocess
import argparse
import json
import sys
import re

ALL_DAY_EVENT_KEY = "All day event"
ALL_DAY_HOLIDAY_KEY = "All day holiday"
# https://stackoverflow.com/a/28938235
COLOUR_OFF = '\033[0m'
COLOUR_BG_BLUE = '\033[44m'
COLOUR_BG_YELLOW = '\033[43m'
COLOUR_GREEN = '\033[0;32m'
COLOUR_PURPLE_BOLD = '\033[1;35m'
COLOUR_LIGHT_GRAY = '\033[0;37m'
COLOUR_DARK_GRAY = '\033[2;37m'
HEADER_COLOUR = COLOUR_BG_BLUE + "{day}" + COLOUR_OFF + "{header}"
ALL_DAY_COLOUR = "    {colour}{name}" + COLOUR_OFF
NORMAL_EVENT_COLOUR = "    {event}"
DONE_EVENT_COLOUR = "    " + COLOUR_DARK_GRAY + "{event}" + COLOUR_OFF
IN_EVENT_COLOUR = (COLOUR_BG_YELLOW + "[*] {event}"
                   + COLOUR_GREEN + "{url}" + COLOUR_OFF)


def filter_sort_event(event_dict: dict) -> list:
    return sorted(
        filter(
            lambda x: isinstance(x[1], dict) and "time" in x[1],
            event_dict.items()
        ), key=lambda v: int(
            re.sub(r'[^\d]*(\d*):?(\d*).*', r'\1\2', v[1]['time']) + '0')
    )


def to_colour(day: str, header: str, event_dict: dict, colour_en: bool) -> str:
    now_h_m = datetime.now().time()
    colour_out_str = HEADER_COLOUR.format(day=day, header=header)

    for k, v in filter_sort_event(event_dict):
        event_time = v.get("time")
        event_name = k[:40]

        if event_time == ALL_DAY_HOLIDAY_KEY:
            colour_str = ALL_DAY_COLOUR.format(
                colour=COLOUR_PURPLE_BOLD, name=f"{event_name} (All day)")
        elif event_time == ALL_DAY_EVENT_KEY:
            colour_str = ALL_DAY_COLOUR.format(
                colour=COLOUR_LIGHT_GRAY, name=f"{event_name} (Not holiday)")
        else:
            event = f"{event_time}  {event_name}"
            reminder_c = datetime.strptime(event_time, "%H:%M")
            reminder_s = (reminder_c - timedelta(minutes=15)).time()
            reminder_e = (reminder_c + timedelta(minutes=5)).time()
            # colour disabled or event not start yet
            if (not colour_en) or (now_h_m < reminder_s):
                colour_str = NORMAL_EVENT_COLOUR.format(event=event)
            elif now_h_m > reminder_e:  # colour enabled and event finished
                colour_str = DONE_EVENT_COLOUR.format(event=event)
            else:  # colour enabled and now in the event
                if url := (v["urls"][1:] or ""):
                    url = "\n    ".join([""] + url)
                colour_str = IN_EVENT_COLOUR.format(event=event, url=url)
        colour_out_str += f"\n{colour_str}"
    return colour_out_str


def get_weather(today_date: datetime) -> str:
    weather_symbol_dict = {
        "SUN": "🔆",
        "LIGHTCLOUD": "🌤️",
        "PARTLYCLOUD": "⛅",
        "CLOUD": "☁️",
        "LIGHTRAINSUN": "🌦️",
        "LIGHTRAINTHUNDERSUN": "🌦️",
        "SLEETSUN": "🌨️",
        "SNOWSUN": "❄️",
        "LIGHTRAIN": "🌧️",
        "RAIN": "🌧️",
        "RAINTHUNDER": "⛈️",
        "SLEET": "🌨️",
        "SNOW": "❄️",
        "SNOWTHUNDER": "❄️",
        "FOG": "🌫️",
        "SLEETSUNTHUNDER": "🌨️",
        "SNOWSUNTHUNDER": "❄️",
        "LIGHTRAINTHUNDER": "🌧️",
        "SLEETTHUNDER": "🌨️"
    }
    weather_time = f"{today_date.strftime('%Y-%m-%dT%H')}:00:00Z"
    re_weather = re.compile(
        r'location_name=(?P<loc>[^,\s]+)[\s\S]+?'
        fr'start={weather_time}\r?\nend={weather_time}'
        r'(?:(?:\r?\n\w+=.+)+?)'
        r'\r?\ntemperature_value=(?P<temperature_value>.+)'
        r'\r?\ntemperature_unit=(?P<temperature_unit>.+)'
        r'\r?\nwind_dir_deg=(?P<wind_dir_deg>.+)'
        r'\r?\nwind_dir_name=(?P<wind_dir_name>.+)'
        r'\r?\nwind_speed_(?P<wind_unit>[^=]+)=(?P<wind_speed>.+)'
        r'[\s\S]+?symbol=(?P<symbol>.+)'
    )
    for f in Path.home().joinpath(".cache/xfce4/weather").glob("weatherdata*"):
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            if weather := [w for w in re_weather.findall(fp.read()) if all(w)]:
                _, t, t_u, _, w_d, w_u, w, s = weather[0]
                t_u = "℃" if "celsius" in t_u.lower() else "℉"
                s = weather_symbol_dict.get(s, s)
                return f"{t}{t_u}  {w_d} wind {w}{w_u}  {s} "
    return str()


def hyperlinks_text(url: str, hyper_txt: str) -> str:
    hyperlinks = '\033]8;{};{}\033\\{}\033]8;;\033\\'
    return hyperlinks.format("", url, hyper_txt)


def search_and_short_url(urls: str, sep=" ") -> str:
    url_list = list()
    for href in re.compile(r'<a href="(?P<url>[^"]+)"').findall(urls):
        if (url := subprocess.run([
            'shorten_url', "--url-min-length=16", re.sub(r'[\s\|]', '', href)
        ], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()) not in url_list:
            url_list.append(url)
    return sep.join(url_list)


def to_date(from_date: datetime, to_format: str = "%Y-%m-%d %a") -> str:
    return from_date.strftime(to_format)


def update_dict_by_key_val(event_dict: dict, key, val: dict):
    if key and val and list(filter(None, val.values())):
        if key in event_dict:
            event_dict[key].update(val)
        else:
            event_dict.update({key: val})


def convert_date_format(date_str: str, from_date: datetime) -> str | None:
    # current only support these two formats
    #  "%a %b %d" is from 'gcalcli agenda'
    #  "%Y-%m-%d" is from 'gcalcli search'
    date_format_list = ["%a %b %d", "%Y-%m-%d"]
    for date_format in date_format_list:
        try:
            event_date = datetime.strptime(date_str.strip(), date_format)
        except ValueError:
            pass
        else:
            event_month = event_date.month
            event_day = event_date.day
            if event_month < from_date.month:
                event_datetime = from_date.replace(
                    year=from_date.year+1, month=event_month, day=event_day)
            else:
                event_datetime = from_date.replace(
                    month=event_month, day=event_day)
            return to_date(event_datetime)
    print(f"{date_str} is not support, can not continue")
    return None


def update_event_dict(date_log: str, today_date: datetime) -> OrderedDict:
    week_a = [(today_date+timedelta(days=i)).strftime("%a") for i in range(7)]
    month_b = [datetime.strptime(str(i).zfill(2), "%m").strftime("%b")
               for i in range(1, 13)]
    re_week_month = f"(?:{'|'.join(week_a)}) (?:{'|'.join(month_b)})"
    re_event = re.compile(
        fr'(?P<date>(?:{re_week_month} |\d+-\d+-)\d+)?'
        r'[ ]+(?P<time>\d{1,2}:\d{2})?[ ]*(?P<event>.+)'
        r'(?:\s+Calendar: (?P<calendar>.+))?'
        r'(?:\s+Link: (?P<link>.+))?'
        r'(?:\s+Hangout Link: (?P<hangout_link>.+))?'
        r'(?:\s+Location: (?P<location>.+))?'
        r'(?:\s+Description:[-+\s]+(?P<description>[^+]+)[-+]+)?'
    )

    cur_date = None
    target_date = None
    cur_date_list = list()
    event_dict = OrderedDict()
    folk_holiday_key = "Folk's holiday"
    folk_holiday_list = list()

    for (
        date, time, event, calendar, link, hangout_link, location, description
    ) in re_event.findall(date_log):
        england_holiday = all([
            "United Kingdom" in calendar,
            "England" in location or "United Kingdom" in location
        ])
        event = re.sub(r'[ ]*\(?(?:regional holiday|all[ ]*day)\)?.*', '',
                       event.strip(), flags=re.IGNORECASE)
        re_meetint_room = r'\(Meeting Room\)-Dale House-(.+?) \('
        if meeting_room := re.findall(re_meetint_room, location):
            event_attr = meeting_room[0].strip()
        elif location and not england_holiday:
            event_attr = location
        else:
            event_attr = None
            re_attr = r'\| (?P<attr>Public holiday|Observance)[ ]+\|'
            if attr := re.findall(re_attr, description):
                event = f"{attr[0]}: {event}"
                if attr[0] == "Public holiday":
                    event_attr = re.sub(
                        "holidays ", "", calendar, flags=re.IGNORECASE)

        event_lower = event.lower()
        cur_event = dict()
        # do not record if event in empty
        # do not record event in "home" or "office"
        # do not record duplicated event
        if all([
                event_lower,
                event_lower not in ("home", "office"),
                event_lower not in cur_date_list
        ]):
            if calendar == "Holiday Calendar":
                folk_holiday_list.append(event)
            else:
                cur_event = {
                    event + (f" ({event_attr})" if event_attr else ""): {
                        "time": time or (
                            ALL_DAY_HOLIDAY_KEY
                            if england_holiday else ALL_DAY_EVENT_KEY),
                        "urls": [link] + list(filter(None, [
                            hangout_link, search_and_short_url(description)]))
                    }
                }
        if date and (date != cur_date):
            update_dict_by_key_val(
                event_dict, target_date, {folk_holiday_key: folk_holiday_list})
            folk_holiday_list = list()
            target_date = convert_date_format(date, today_date)
            cur_date_list = [event_lower]
            cur_date = date
        else:
            cur_date_list.append(event_lower)

        update_dict_by_key_val(event_dict, target_date, cur_event)
    update_dict_by_key_val(
        event_dict, target_date, {folk_holiday_key: folk_holiday_list})
    return event_dict


def remove_colour(input_str: str) -> str:
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", input_str).strip()


def update_from_file(event_dict, days_later: int) -> dict:
    re_holiday = r'(?P<name>.*holiday.*)\((?P<duration>\d+) day[s]*\)'
    file_holiday = dict()
    for k, v in event_dict.items():
        for name, duration in re.findall(re_holiday, k, re.IGNORECASE):
            if (left_day := int(duration) - days_later) > 0:
                day_label = 'days' if left_day > 1 else 'day'
                file_holiday.update({f"{name} ({left_day} {day_label})": v})
    return file_holiday


def set_days_later(days_later: int, today_date: datetime) -> int:
    if days_later < 0:
        week_num = today_date.isoweekday()
        if (week_num > 5) or (week_num == 5 and today_date.hour > 16):
            # display next Monday's event from Friday's afternoon
            days_later = 8 - week_num
        else:
            # display tomorrow event after 17:00
            days_later = 1 if today_date.hour > 16 else 0
    return days_later


def main_out_agenda(event_dict, today_date, days_later, weather) -> None:
    event_date = today_date + timedelta(days=days_later)
    w_m_d = to_date(event_date)
    day_event_dict = event_dict.get(w_m_d) or {
        "Weekend" if event_date.isoweekday() > 5 else "No Event found": {
            "time": ALL_DAY_HOLIDAY_KEY
        }
    }
    headers = [weather, "tomorrow", f"{days_later} days later"]
    h = headers[days_later if days_later < len(headers) else -1]
    print(to_colour(w_m_d, f" ({h})", day_event_dict, days_later == 0))


def parse_arguments(filename: str):
    parser = argparse.ArgumentParser(
        description="Filter gcalcli agenda message")
    parser.add_argument(
        "--out-event-only", dest="out_event_only", action="store_true",
        help="Output today's event only")
    parser.add_argument(
        "--from-file", dest="from_file", action="store_true", default=False,
        help=f"Read agenda message from file {filename}")
    parser.add_argument(
        "--days-later", dest="days_later", type=int, default=-1,
        help="Display n days later agenda, must be within 30 days")
    return parser.parse_args()


if __name__ == "__main__":
    GCALCLI_FILENAME = "/tmp/gcalcli_agenda.json"
    args = parse_arguments(GCALCLI_FILENAME)
    today_date = datetime.today()
    weather = get_weather(today_date)
    today_key = to_date(today_date)
    if (days_later := set_days_later(args.days_later, today_date)) > 0:
        days_later_key = to_date(today_date + timedelta(days=days_later))
    else:
        days_later_key = today_key
    from_file_flag = args.from_file or sys.stdin.isatty()

    try:
        with open(GCALCLI_FILENAME,
                  "r", encoding="utf-8", errors="ignore") as f:
            from_file_event_dict = json.load(f)
    except FileNotFoundError:
        from_file_event_dict = {}

    if from_file_flag:
        if from_file_event_dict:
            event_dict = from_file_event_dict
        else:
            print(f"No stdin and {GCALCLI_FILENAME} available")
            exit()
    else:
        event_dict = update_event_dict(remove_colour(
            sys.stdin.buffer.read().decode('utf-8', 'ignore')), today_date)

    if days_later > 0 and (file_today := from_file_event_dict.get(today_key)):
        update_dict_by_key_val(event_dict, days_later_key, update_from_file(
            file_today, days_later)
        )

    if args.out_event_only:
        if days_later == 0:
            print(f"weather: {weather}")
        for k, v in filter_sort_event(event_dict.get(days_later_key, {})):
            print(f"{v.get('time')}: {k}")
    else:
        main_out_agenda(event_dict, today_date, days_later, weather)
        if (not from_file_flag) and (event_dict != from_file_event_dict):
            with open(GCALCLI_FILENAME, "w", encoding="utf-8") as f:
                json.dump(event_dict, f, indent=4)
